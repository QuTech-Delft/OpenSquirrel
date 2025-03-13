from abc import ABC, abstractmethod

from opensquirrel.ir import IR


class Router(ABC):
    @abstractmethod
    def route(self, ir: IR) -> IR:
        raise NotImplementedError
