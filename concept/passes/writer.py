from abc import ABC, abstractmethod

class Writer(ABC):

    @classmethod
    @abstractmethod
    def apply(cls, ast: str) -> str:
        raise NotImplementedError

class WriterX(Writer):

    @classmethod
    def apply(cls, ast: str) -> str:
        return ast[4:] + "_written_by_X"
