from abc import ABC, abstractmethod

from opensquirrel.ir import IR


class Checker(ABC):
    @abstractmethod
    def check(self, ir: IR) -> None:
        raise NotImplementedError
