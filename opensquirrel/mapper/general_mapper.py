"""This module contains generic mapping components."""

from __future__ import annotations

from opensquirrel.mapping import Mapping
from opensquirrel.register_manager import PhysicalQubitRegister


class Mapper:
    """Base class for the Mapper pass."""

    def __init__(self, qubit_register_size: int, mapping: Mapping = None) -> None:
        """Use ``IdentityMapper`` as the fallback case for ``Mapper``"""
        self.mapping = mapping if mapping is not None else Mapping(PhysicalQubitRegister(range(qubit_register_size)))

        if qubit_register_size != self.mapping.size():
            raise ValueError("Qubit register size and mapping size differ.")

    def get_mapping(self) -> Mapping:
        """Get mapping."""
        return self.mapping
