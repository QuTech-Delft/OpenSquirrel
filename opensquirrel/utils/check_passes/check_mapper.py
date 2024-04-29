"""This module contains checks for the ``Mapper`` pass."""

from copy import deepcopy

from opensquirrel.mapper.general_mapper import Mapper
from opensquirrel.squirrel_ir import BlochSphereRotation, Comment, ControlledGate, Measure, Qubit, SquirrelIR


def check_mapper(mapper: Mapper) -> None:
    """Check if the `mapper` complies with the OpenSquirrel requirements.

    If an implementation of ``Mapper`` passes these checks it should be compatible with the ``Circuit.map_qubits``
    method.

    Args:
        mapper: Mapper to check.
    """

    assert isinstance(mapper, Mapper)

    squirrel_ir = SquirrelIR(number_of_qubits=10)
    _check_scenario(squirrel_ir, deepcopy(mapper))

    squirrel_ir = SquirrelIR(number_of_qubits=10)
    squirrel_ir.add_comment(Comment("comment"))
    squirrel_ir.add_gate(BlochSphereRotation(Qubit(42), (1, 0, 0), 1, 2))
    squirrel_ir.add_gate(ControlledGate(Qubit(42), BlochSphereRotation.identity(Qubit(100))))
    squirrel_ir.add_measurement(Measure(Qubit(42), (0, 0, 1)))
    _check_scenario(squirrel_ir, deepcopy(mapper))


def _check_scenario(squirrel_ir: SquirrelIR, mapper: Mapper) -> None:
    """Check if the given scenario can be mapped.

    Args:
        squirrel_ir: SquirrelIR containing the scenario to check against.
        mapping: Mapping to check.
    """
    squirrel_ir_copy = deepcopy(squirrel_ir)
    mapping = mapper.map(squirrel_ir)

    assert squirrel_ir == squirrel_ir_copy, "A Mapper pass should not change the SquirrelIR"
    _check_mapping_format(mapping, squirrel_ir.number_of_qubits)


def _check_mapping_format(mapping: dict[int, int], n_qubits: int) -> None:
    """Check if the mapping has the expected format.

    Args:
        mapping: Mapping to check.
        n_qubits: Number of qubits in the circuit.
    """
    assert isinstance(
        mapping, dict
    ), f"Output mapping should be an instance of <class 'dict'>, but was of type {type(mapping)}"
    assert set(mapping.keys()) == set(
        mapping.values()
    ), "The set of virtual qubits is not equal to the set of phyical qubits."
    assert set(range(n_qubits)) == set(mapping.keys()), "Virtual qubits are not labeled correctly."
