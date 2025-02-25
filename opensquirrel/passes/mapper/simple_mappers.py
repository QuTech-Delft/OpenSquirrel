"""This module contains the following simple mappers:

* IdentityMapper
* HardcodedMapper
* RandomMapper
"""

import random

from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping


class IdentityMapper(Mapper):
    def __init__(self, qubit_register_size: int) -> None:
        """An ``IdentityMapper`` maps each virtual qubit to exactly the same physical qubit."""
        super().__init__(qubit_register_size)


class HardcodedMapper(Mapper):
    def __init__(self, qubit_register_size: int, mapping: Mapping) -> None:
        """A ``HardcodedMapper`` maps each virtual qubit to a hardcoded physical qubit"""
        super().__init__(qubit_register_size, mapping)


class RandomMapper(Mapper):
    def __init__(self, qubit_register_size: int) -> None:
        """A ``RandomMapper`` maps each virtual qubit to a random physical qubit."""
        physical_qubit_register = list(range(qubit_register_size))
        random.shuffle(physical_qubit_register)
        random_mapping = Mapping(physical_qubit_register)
        super().__init__(qubit_register_size, random_mapping)
