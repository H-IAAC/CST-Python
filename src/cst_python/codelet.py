import abc

from cst_python.memory import Memory

class Codelet(abc.ABC):

    def get_input(self) -> Memory:
        pass

    def get_output(self) -> Memory:
        pass

    def add_input(self, memory:Memory) -> None:
        pass
    
    def add_output(self, memory:Memory) -> None:
        pass

    @abc.abstractmethod
    def proc(self) -> None:
        ...

    @abc.abstractmethod
    def access_memory_objects(self) -> None:
        ...
    
    @abc.abstractmethod
    def calculate_activation(self) -> None:
        ...