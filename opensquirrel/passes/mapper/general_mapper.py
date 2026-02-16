"""This module contains generic mapping components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opensquirrel.ir import IR
    from opensquirrel.passes.mapper.mapping import Mapping


class Mapper(ABC):
    """Base class for the Mapper pass."""

    uses_interaction_graph = False

    def __init__(self, **kwargs: Any) -> None: ...

    @abstractmethod
    def map(
        self,
        ir: IR,
        qubit_register_size: int,
        interaction_graph: dict[tuple[int, int], int] | None = None,
    ) -> Mapping:
        raise NotImplementedError
