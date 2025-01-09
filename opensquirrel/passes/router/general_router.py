from abc import ABC, abstractmethod


class Router(ABC):
    @abstractmethod
    def route(self, interactions: list[tuple[int, int]]) -> None:
        pass
