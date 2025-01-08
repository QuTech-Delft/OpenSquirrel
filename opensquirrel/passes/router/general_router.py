from abc import ABC, abstractmethod
from typing import Any


class Router(ABC):
    @abstractmethod
    def route(self, *args: Any, **kwargs: Any) -> None:
        pass
