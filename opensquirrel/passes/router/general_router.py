from abc import ABC, abstractmethod
from typing import Any

from opensquirrel import Connectivity
from opensquirrel.ir import IR


class Router(ABC):
    def __init__(self, connectivity: Connectivity, **kwargs: Any) -> None:
        self._connectivity = connectivity
        """Generic router class"""

    @abstractmethod
    def route(self, ir: IR, qubit_register_size: int) -> IR:
        raise NotImplementedError
