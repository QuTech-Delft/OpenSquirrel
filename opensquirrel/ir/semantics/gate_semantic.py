from abc import ABC, abstractmethod


class GateSemantic(ABC):
    @abstractmethod
    def is_identity(self) -> bool:
        pass


class MatrixSemantic(GateSemantic):
    def is_identity(self) -> bool:
        return False
