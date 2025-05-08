from abc import ABC, abstractmethod
from typing import Any

from opensquirrel.ir import IR


class Validator(ABC):
    def __init__(self, **kwargs: Any) -> None: ...

    @abstractmethod
    def validate(self, ir: IR) -> None:
        """Base validate method to be implemented by inheriting validator classes."""
        raise NotImplementedError
