"""This module contains generic mapping components."""

from __future__ import annotations

from abc import ABC, abstractmethod

from opensquirrel.squirrel_ir import Gate, Measure, SquirrelIR


def map_qubits(squirrel_ir: SquirrelIR, mapper: Mapper) -> None:
    """Map the virtual qubits in the `squirrel_ir` to physical qubits using `mapper`.

    Args:
        squirrel_ir: IR to apply mapping to.
        mapper: Mapping pass to use.
    """

    mapping = mapper.map(squirrel_ir)

    for statement in squirrel_ir.statements:
        if isinstance(statement, (Gate, Measure)):
            statement.relabel(mapping)


class Mapper(ABC):
    """Base class for the Mapper pass."""

    @abstractmethod
    def map(self, squirrel_ir: SquirrelIR) -> dict[int, int]:
        """Produce a mapping from the virtual qubits in the `squirrel_ir` to the physical qubits.

        Args:
            squirrel_ir: IR to apply mapping to.

        Returns:
            Mapping from virtual qubits to physical qubits.
        """
