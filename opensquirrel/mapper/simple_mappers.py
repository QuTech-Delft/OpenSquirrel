"""This module contains the following simple mappers:

* IdentityMapper
* HardcodedMapper
"""

from collections.abc import Mapping
from typing import SupportsInt

from opensquirrel.mapper.general_mapper import Mapper
from opensquirrel.squirrel_ir import SquirrelIR


class IdentityMapper(Mapper):

    def map(self, squirrel_ir: SquirrelIR) -> dict[int, int]:
        """Produce an IdentityMapping.

        Args:
            squirrel_ir: IR to map.

        Returns:
            Dictionary with as keys the virtual qubits and as values the physical qubits. The dictionary maps each
            virtual qubit to exactly the same physical qubit.
        """
        return {i: i for i in range(squirrel_ir.number_of_qubits)}


class HardcodedMapper(Mapper):

    def __init__(self, mapping: Mapping[SupportsInt, SupportsInt]) -> None:
        """Init of the ``HardcodedMapper``.

        Args:
            mapping: Mapping with as keys the virtual qubits and as values the physical qubits.

        Raises:
            ValueError: If `mapping` is not a valid mapping.
        """
        # Check if the provided mapping is valid
        self.mapping = {int(virtual_qubit): int(physical_qubit) for virtual_qubit, physical_qubit in mapping.items()}
        if set(self.mapping.keys()) != set(self.mapping.values()):
            raise ValueError("The set of physical qubits is not equal to the set of virtual qubits.")

    def map(self, squirrel_ir: SquirrelIR) -> dict[int, int]:
        """Retrieve tha hardcoded mapping.

        Args:
            squirrel_ir: IR to map.

        Returns:
            Dictionary with as keys the virtual qubits and as values the physical qubits.
        """
        if set(range(squirrel_ir.number_of_qubits)) != set(self.mapping.keys()):
            raise ValueError("Virtual qubits are not labeled correctly.")

        return self.mapping
