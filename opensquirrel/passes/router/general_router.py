from abc import ABC, abstractmethod

from opensquirrel.ir import IR


class Router(ABC):
    @abstractmethod
    def route(self, ir: IR) -> None:
        raise NotImplementedError
