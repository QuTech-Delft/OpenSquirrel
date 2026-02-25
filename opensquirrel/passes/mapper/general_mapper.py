"""This module contains generic mapping components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opensquirrel import Circuit
    from opensquirrel.passes.mapper.mapping import Mapping


class Mapper(ABC):
    """Base class for the Mapper pass."""

    def __init__(self, **kwargs: Any) -> None: ...

    @abstractmethod
    def map(
        self,
        circuit: Circuit,
        qubit_register_size: int,
    ) -> Mapping:
        raise NotImplementedError
