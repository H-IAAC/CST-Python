import json
from typing import Any

from cst_python.core.entities import Memory

class MemoryEncoder(json.JSONEncoder):
    def default(self, memory:Memory):
        return MemoryEncoder.to_dict(memory)
    
    @staticmethod
    def to_dict(memory:Memory, jsonify_info:bool=False):
        data = {
            "timestamp": memory.get_timestamp(),
            "evaluation": memory.get_evaluation(),
            "I": memory.get_info(),
            "name": memory.get_name(),
            "id": memory.get_id()
        }

        if jsonify_info:
            data["I"] = json.dumps(data["I"])

        return data
    
    def load_memory(memory:Memory, memory_dict:dict[str,Any], load_json:bool=True):
        memory.set_evaluation(float(memory_dict["evaluation"]))
        memory.set_id(int(memory_dict["id"]))

        info_json = memory_dict["I"]
        info = json.loads(info_json)

        memory.set_info(info)
