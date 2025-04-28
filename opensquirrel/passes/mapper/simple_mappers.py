"""This module contains the following simple mappers:

* IdentityMapper
* HardcodedMapper
* RandomMapper
"""

import random
from typing import Any

from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping


class IdentityMapper(Mapper):
    def __init__(self, qubit_register_size: int, **kwargs: Any) -> None:
        """An ``IdentityMapper`` maps each virtual qubit to exactly the same physical qubit."""
        super().__init__(qubit_register_size, **kwargs)


class HardcodedMapper(Mapper):
    def __init__(self, qubit_register_size: int, mapping: Mapping, **kwargs: Any) -> None:
        """
        A ``HardcodedMapper`` maps each virtual qubit to a hardcoded physical qubit

        Args:
            qubit_register_size: The number of qubits in the physical qubit register
            mapping: The mapping from virtual to physical qubits
        """
        super().__init__(qubit_register_size, mapping, **kwargs)


class RandomMapper(Mapper):
    def __init__(self, qubit_register_size: int, **kwargs: Any) -> None:
        """
        A ``RandomMapper`` maps each virtual qubit to a random physical qubit.

        Args:
            qubit_register_size: The number of qubits in the physical qubit register
        """
        physical_qubit_register = list(range(qubit_register_size))
        random.shuffle(physical_qubit_register)
        random_mapping = Mapping(physical_qubit_register)
        super().__init__(qubit_register_size, random_mapping, **kwargs)
