"""This module contains generic mapping components."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opensquirrel.ir import IR
    from opensquirrel.passes.mapper.mapping import Mapping


class Mapper:
    """Base class for the Mapper pass."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the mapper."""

    def get_mapping(self, ir: IR, qubit_register_size: int) -> Mapping:
        """Get mapping."""
        return self.map(ir, qubit_register_size)

    def map(self, ir: IR, qubit_register_size: int) -> Mapping:
        raise NotImplementedError()
