from abc import ABC, abstractmethod


class GateSemantic(ABC):
    @abstractmethod
    def is_identity(self) -> bool:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass
