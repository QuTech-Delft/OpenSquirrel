from abc import ABC, abstractmethod
from typing import Any

from opensquirrel.ir import IR


class Router(ABC):
    def __init__(self, **kwargs: Any) -> None: ...

    @abstractmethod
    def route(self, ir: IR) -> IR:
        raise NotImplementedError
