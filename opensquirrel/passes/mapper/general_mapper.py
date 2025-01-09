"""This module contains generic mapping components."""

from __future__ import annotations

from opensquirrel.passes.mapper.mapping import Mapping


class Mapper:
    """Base class for the Mapper pass."""

    def __init__(self, qubit_register_size: int, mapping: Mapping | None = None) -> None:
        """Use ``IdentityMapper`` as the fallback case for ``Mapper``"""
        physical_qubit_register = list(range(qubit_register_size))
        self.mapping = mapping if mapping is not None else Mapping(physical_qubit_register)

        if qubit_register_size != self.mapping.size():
            msg = "qubit register size and mapping size differ"
            raise ValueError(msg)

    def get_mapping(self) -> Mapping:
        """Get mapping."""
        return self.mapping
