from abc import ABC, abstractmethod
from typing import Any

from opensquirrel.ir import IR


class Router(ABC):
    def __init__(self, **kwargs: Any) -> None:
        """ Router class to map a quantum algorithm on the specific topology """
        ...

    @abstractmethod
    def route(self, ir: IR) -> IR:
        raise NotImplementedError
