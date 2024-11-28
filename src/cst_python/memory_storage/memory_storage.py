import json
import weakref
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import logging
import functools
from typing import Optional, cast

import redis

from cst_python.core.entities import Codelet, Mind, Memory, MemoryObject
from .memory_encoder import MemoryEncoder

logger = logging.getLogger("MemoryStorageCodelet")
logger.setLevel(logging.DEBUG)

class MemoryStorageCodelet(Codelet):
    def __init__(self, mind:Mind, node_name:Optional[str]=None, mind_name:Optional[str]=None, request_timeout:float=500e-3) -> None:
        super().__init__()
        
        self._mind = mind
        self._request_timeout = request_timeout
        
        if mind_name is None:
            mind_name = "default_mind"
        self._mind_name = cast(str, mind_name)
        
        self._memories : weakref.WeakValueDictionary[str, Memory] = weakref.WeakValueDictionary()
        
        self._client = redis.Redis(decode_responses=True)
        self._pubsub = self._client.pubsub()
        self._pubsub_thread : redis.client.PubSubWorkerThread = self._pubsub.run_in_thread()

        if node_name is None:
            node_name = "node"
        base_name = node_name
        
        if self._client.sismember(f"{mind_name}:nodes", node_name):
            node_number = self._client.scard(f"{mind_name}:nodes")
            node_name = base_name+str(node_number)
            while self._client.sismember(f"{mind_name}:nodes", node_name):
                node_number += 1
                node_name = base_name+str(node_number)
            

        self._node_name = cast(str, node_name)

        self._client.sadd(f"{mind_name}:nodes", node_name)

        transfer_service_addr = f"{self._mind_name}:nodes:{node_name}:transfer_memory"
        self._pubsub.subscribe(**{transfer_service_addr:self._handler_transfer_memory})

        transfer_done_addr = f"{self._mind_name}:nodes:{node_name}:transfer_done"
        self._pubsub.subscribe(**{transfer_done_addr:self._handler_notify_transfer})

        self._last_update : dict[str, int] = {}
        self._waiting_retrieve : set[str] = set()
        
        self._retrieve_executor = ThreadPoolExecutor(3)

        self._waiting_request_events : dict[str, threading.Event] = {}

        self._request = None

    def calculate_activation(self) -> None: #NOSONAR
        pass

    def access_memory_objects(self) -> None: #NOSONAR
        pass

    def proc(self) -> None:
        
        #Check new memories

        mind_memories : dict[str, Memory] = {}
        for memory in self._mind.raw_memory.all_memories:
            if memory.get_name() == "": #No name -> No MS
                continue

            mind_memories[memory.get_name()] = memory

        mind_memories_names = set(mind_memories.keys())
        memories_names = set(self._memories.keys())

        #Check only not here (memories_names not in mind should be garbage collected)
        difference = mind_memories_names - memories_names
        for memory_name in difference:
            memory = mind_memories[memory_name]
            self._memories[memory_name] = memory

            if self._client.exists(f"{self._mind_name}:memories:{memory_name}"):
                self._retrieve_executor.submit(self._retrieve_memory, memory)
                
            else: #Send impostor with owner
                memory_impostor : dict[str|bytes, str|float|int] = {"name":memory.get_name(),
                                   "evaluation" : 0.0,
                                   "I": "",
                                   "id" : 0,
                                   "owner": self._node_name}
                
                self._client.hset(f"{self._mind_name}:memories:{memory_name}", mapping=memory_impostor)

            subscribe_func = lambda _, name : self.update_memory(name)
            subscribe_func = functools.partial(subscribe_func, name=memory_name)
            self._pubsub.subscribe(**{f"{self._mind_name}:memories:{memory_name}:update":subscribe_func})

        #Update memories
        to_update = self._last_update.keys()
        for memory_name in to_update:
            if memory_name not in self._memories:
                del self._last_update[memory_name]
                continue

            memory = self._memories[memory_name]
            if memory.get_timestamp() > self._last_update[memory_name]:
                self.update_memory(memory_name)

    def update_memory(self, memory_name:str) -> None:
        logger.info(f"Updating memory [{memory_name}@{self._node_name}]")

        if memory_name not in self._memories:
            self._pubsub.unsubscribe(f"{self._mind_name}:memories:{memory_name}:update")

        timestamp_result = self._client.hget(f"{self._mind_name}:memories:{memory_name}", "timestamp")
        assert timestamp_result is not None
        timestamp = float(timestamp_result)
        memory = self._memories[memory_name]
        memory_timestamp = memory.get_timestamp()
        
        if memory_timestamp < timestamp:
            self._retrieve_executor.submit(self._retrieve_memory, memory)

        elif memory_timestamp> timestamp:
            self._send_memory(memory)

        self._last_update[memory_name] = memory.get_timestamp()

    def _send_memory(self, memory:Memory) -> None:
        memory_name = memory.get_name()
        logger.info(f"Sending memory [{memory_name}@{self._node_name}]")

        memory_dict = MemoryEncoder.to_dict(memory, jsonify_info=True)
        memory_dict["owner"] = ""


        self._client.hset(f"{self._mind_name}:memories:{memory_name}", mapping=memory_dict)
        self._client.publish(f"{self._mind_name}:memories:{memory_name}:update", "")

        self._last_update[memory_name] = memory.get_timestamp()
        

    def _retrieve_memory(self, memory:Memory) -> None:
        memory_name = memory.get_name()
        logger.info(f"Retrieving memory [{memory_name}@{self._node_name}]")

        if memory_name in self._waiting_retrieve:
            return
        self._waiting_retrieve.add(memory_name)

        memory_dict = self._client.hgetall(f"{self._mind_name}:memories:{memory_name}")

        if memory_dict["owner"] != "":
            event = threading.Event()
            self._waiting_request_events[memory_name] = event
            self._request_memory(memory_name, memory_dict["owner"])

            if not event.wait(timeout=self._request_timeout):
                logger.warning(f"Request failed [{memory_name}@{memory_dict['owner']} to {self._node_name}]")
                #Request failed
                self._send_memory(memory)
                return 
            
            memory_dict = self._client.hgetall(f"{self._mind_name}:memories:{memory_name}")

        MemoryEncoder.load_memory(memory, memory_dict)

        self._last_update[memory_name] = memory.get_timestamp()

        self._waiting_retrieve.remove(memory_name)

    def _request_memory(self, memory_name:str, owner_name:str) -> None:
        logger.info(f"Requesting memory [{memory_name}@{owner_name} to {self._node_name}]")

        request_addr = f"{self._mind_name}:nodes:{owner_name}:transfer_memory"
        
        request_dict = {"memory_name":memory_name, "node":self._node_name}
        request = json.dumps(request_dict)
        self._client.publish(request_addr, request)

    def _handler_notify_transfer(self, message:dict[str,str]) -> None:
        memory_name = message["data"]
        if memory_name in self._waiting_request_events:
            event = self._waiting_request_events[memory_name]
            event.set()
            del self._waiting_request_events[memory_name]

    def _handler_transfer_memory(self, message:dict[str,str]) -> None:
        request = json.loads(message["data"])
        
        memory_name = request["memory_name"]
        requesting_node = request["node"]

        logger.info(f"Transfering memory to server [{memory_name}@{self._node_name}]")

        if memory_name in self._memories:
            memory = self._memories[memory_name]
        else:
            memory = MemoryObject()
            memory.set_name(memory_name)
        
        self._send_memory(memory)

        response_addr = f"{self._mind_name}:nodes:{requesting_node}:transfer_done"
        self._client.publish(response_addr, memory_name)

    def __del__(self) -> None:
        self._pubsub_thread.stop()
        self._retrieve_executor.shutdown(cancel_futures=True)