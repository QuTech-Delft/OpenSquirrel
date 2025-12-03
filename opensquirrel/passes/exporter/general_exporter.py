from abc import ABC, abstractmethod
from typing import Any

from opensquirrel import Circuit


class Exporter(ABC):
    def __init__(self, **kwargs: Any) -> None:
        """Generic router class"""

    @abstractmethod
    def export(self, circuit: Circuit) -> Any:
        raise NotImplementedError
