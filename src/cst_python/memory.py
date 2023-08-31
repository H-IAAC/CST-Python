import abc
from typing import Any

class Memory(abc.ABC):
    
    @abc.abstractmethod
    def get_info(self) -> Any:
        ...
    
    @abc.abstractmethod
    def set_info(self, value) -> None:
        ...