import abc
import functools

from typing import Self

class LogicalTime(abc.ABC):

    @abc.abstractmethod
    def increment(self) -> "LogicalTime":
        ...


    @abc.abstractmethod
    def __str__(self) -> str:
        ...
    
    @classmethod
    @abc.abstractmethod
    def from_str(cls, string:str) -> "LogicalTime":
        ...

    @classmethod
    @abc.abstractmethod
    def syncronize(cls, time0:Self, time1:Self) -> "LogicalTime":
        ...

    @abc.abstractmethod
    def __eq__(self, other) -> bool:
        ...
    
    @abc.abstractmethod
    def __lt__(self, other) -> bool:
        ...

    @abc.abstractmethod
    def __le__(self, other) -> bool:
        ...

    @abc.abstractmethod
    def __gt__(self, other) -> bool:
        ...

    @abc.abstractmethod
    def __ge__(self, other) -> bool:
        ...


@functools.total_ordering
class LamportTime(LogicalTime):

    #Methods that total_ordering will overwrite
    __le__ = object.__lt__ # type: ignore
    __gt__ = object.__gt__ # type: ignore
    __ge__ = object.__ge__ # type: ignore


    def __init__(self, initial_time:int=0):
        super().__init__()
        self._time = initial_time

    def increment(self) -> "LamportTime":
        return LamportTime(initial_time=self._time+1)

    def __eq__(self, other) -> bool:
        return self._time == other._time

    def __lt__(self, other) -> bool:
        return self._time < other._time   

    def __str__(self) -> str:
        return str(self._time)

    @classmethod
    def from_str(cls, string:str) -> "LamportTime":
        return LamportTime(int(string))

    @classmethod
    def syncronize(cls, time0:Self, time1:Self) -> "LamportTime":
        new_time = 0
        if time0 < time1:
            new_time = time1._time
        else:
            new_time = time0._time

        new_time += 1

        return LamportTime(new_time)