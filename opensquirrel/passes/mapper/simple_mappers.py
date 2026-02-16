"""This module contains the following simple mappers:

* IdentityMapper
* HardcodedMapper
* RandomMapper
"""

from __future__ import annotations

import random
import warnings
from typing import TYPE_CHECKING, Any

from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping

if TYPE_CHECKING:
    from opensquirrel.ir import IR


class IdentityMapper(Mapper):
    def __init__(self, **kwargs: Any) -> None:
        """An ``IdentityMapper`` maps each virtual qubit to exactly the same physical qubit."""
        super().__init__(**kwargs)

    def map(
        self,
        ir: IR,
        qubit_register_size: int,
        interaction_graph: dict[tuple[int, int], int] | None = None,
    ) -> Mapping:
        """Create identity mapping."""
        if interaction_graph is not None:
            msg = (
                "The IdentityMapper does not effectively use the interaction graph, "
                "thus this argument should be set to None"
            )
            warnings.warn(msg, stacklevel=2)
        return Mapping(list(range(qubit_register_size)))


class HardcodedMapper(Mapper):
    def __init__(self, mapping: Mapping, **kwargs: Any) -> None:
        """
        A ``HardcodedMapper`` maps each virtual qubit to a hardcoded physical qubit

        Args:
            mapping: The mapping from virtual to physical qubits
        """
        super().__init__(**kwargs)
        self._mapping = mapping

    def map(
        self,
        ir: IR,
        qubit_register_size: int,
        interaction_graph: dict[tuple[int, int], int] | None = None,
    ) -> Mapping:
        """Return the hardcoded mapping."""
        if interaction_graph is not None:
            msg = (
                "The HardcodedMapper does not effectively use the interaction graph, "
                "thus this argument should be set to None"
            )
            warnings.warn(msg, stacklevel=2)
        if qubit_register_size != self._mapping.size():
            msg = (
                f"the size of the mapping {self._mapping.size()!r} is not equal to the number of qubits"
                f" {qubit_register_size!r}"
            )
            raise ValueError(msg)
        return self._mapping


class RandomMapper(Mapper):
    def __init__(self, seed: int | None = None, **kwargs: Any) -> None:
        """
        A ``RandomMapper`` maps each virtual qubit to a random physical qubit.

        Args:
            seed: Random seed for reproducible results
        """
        super().__init__(**kwargs)
        self.seed = seed

    def map(
        self,
        ir: IR,
        qubit_register_size: int,
        interaction_graph: dict[tuple[int, int], int] | None = None,
    ) -> Mapping:
        """Create a random mapping."""
        if interaction_graph is not None:
            msg = (
                "The RandomMapper does not effectively use the interaction graph, "
                "thus this argument should be set to None"
            )
            warnings.warn(msg, stacklevel=2)
        if self.seed:
            random.seed(self.seed)

        physical_qubit_register = list(range(qubit_register_size))
        random.shuffle(physical_qubit_register)
        return Mapping(physical_qubit_register)
