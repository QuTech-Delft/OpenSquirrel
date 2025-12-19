from abc import ABC, abstractmethod

from opensquirrel.ir import IRNode


class GateSemantic(IRNode, ABC):
    @abstractmethod
    def is_identity(self) -> bool:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass
