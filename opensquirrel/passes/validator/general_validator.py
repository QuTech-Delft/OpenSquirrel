from abc import ABC, abstractmethod

from opensquirrel.ir import IR


class Validator(ABC):
    @abstractmethod
    def validate(self, ir: IR) -> None:
        """Base validate method to be implemented by inheriting validator classes."""
        raise NotImplementedError
