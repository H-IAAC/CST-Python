from __future__ import annotations

import time
from typing import Any, Set

from cst_python.python import alias
from .memory import Memory
from .memory_observer import MemoryObserver

class MemoryObject(Memory):

    def __init__(self) -> None:
        self._id = 0.0
        self._timestamp = 0.0
        self._evaluation = 0.0
        self._info : Any = None
        self._name = ""
        self._memory_observers : Set[MemoryObserver] = set()

    def __getstate__(self) -> object:
        state = dict(self.__dict__)

        del state["_memory_observers"]

        return state
    
    def get_id(self) -> float:
        return self._id
    
    def set_id(self, memory_id: float) -> None:
        self._id = memory_id

    def get_info(self) -> Any:
        return self._info
    
    def set_info(self, value: Any) -> int:
        self._info = value
        self._timestamp = time.time()
        self._notify_memory_observers()

        return -1

    def _notify_memory_observers(self) -> None:
        for observer in self._memory_observers:
            observer.notify_codelet()

    def update_info(self, info:Any) -> None:
        self.set_info(info)

    def get_timestamp(self) -> float:
        return self._timestamp

    @property
    def timestamp(self) -> float:
        return self._timestamp

    #@alias.alias("setTimestamp")
    @timestamp.setter
    def timestamp(self, value:float) -> None:
        self._timestamp = value

    def get_name(self) -> str:
        return self._name

    def set_type(self, name:str) -> None:
        self._name = name

    def set_name(self, name: str) -> None:
        self._name = name

    def get_evaluation(self) -> float:
        return self._evaluation

    def set_evaluation(self, evaluation: float) -> None:
        return self._evaluation

    #@alias.alias("toString", "to_string")
    def __str__(self) -> str:
        return f"MemoryObject [idmemoryobject={self._id}, \
                timestamp={self._timestamp}, evaluation={self._evaluation}, \
                I={self._info}, name={self._name}]"
    
    #@alias.alias("hashCode", "hash_code")
    def __hash__(self) -> int:
        prime = 31
        result = 1

        result = prime * result + ( 0 if self._info is None else hash(self._info))
        result = prime * result + ( hash(self._evaluation))
        result = prime * result + ( hash(self._id))
        result = prime * result + ( hash(self._name))
        result = prime * result + ( hash(self._timestamp))

        return result
    
    #@alias.alias("equals")
    def __eq__(self, value: MemoryObject) -> bool:
        if id(self) == id(value):
            return True
        if value is None:
            return False
        if type(self) != type(value):
            return False

        compare_list = ["_info", "_evaluation", "_id", "_name", "_timestamp"]

        for name in compare_list:
            self_attr = getattr(self, name)
            other_attr = getattr(value, name)

            if self_attr is None and other_attr is not None:
                return False
            elif self_attr != other_attr:
                return False

        return True


    def add_memory_observer(self, observer: MemoryObserver) -> None:
        self._memory_observers.add(observer)

    def remove_memory_observer(self, observer: MemoryObserver) -> None:
        self._memory_observers.remove(observer)