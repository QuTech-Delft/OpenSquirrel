"""This module contains checks for the ``Mapper`` pass."""

from __future__ import annotations

from copy import deepcopy

from opensquirrel.circuit import Circuit
from opensquirrel.mapper.general_mapper import Mapper
from opensquirrel.mapper.mapping import Mapping
from opensquirrel.register_manager import RegisterManager
from opensquirrel.squirrel_ir import BlochSphereRotation, Comment, ControlledGate, Measure, Qubit, SquirrelIR


def check_mapper(mapper: Mapper) -> None:
    """Check if the `mapper` complies with the OpenSquirrel requirements.

    If an implementation of ``Mapper`` passes these checks it should be compatible with the ``Circuit.map`` method.

    Args:
        mapper: Mapper to check.
    """
    assert isinstance(mapper, Mapper)

    register_manager = RegisterManager(qubit_register_size=10)
    squirrel_ir = SquirrelIR()
    circuit = Circuit(register_manager, squirrel_ir)
    _check_scenario(circuit, mapper)

    squirrel_ir = SquirrelIR()
    squirrel_ir.add_comment(Comment("comment"))
    squirrel_ir.add_gate(BlochSphereRotation(Qubit(42), (1, 0, 0), 1, 2))
    squirrel_ir.add_gate(ControlledGate(Qubit(42), BlochSphereRotation.identity(Qubit(100))))
    squirrel_ir.add_measurement(Measure(Qubit(42), (0, 0, 1)))
    Circuit(register_manager, squirrel_ir)
    _check_scenario(circuit, mapper)


def _check_scenario(circuit: Circuit, mapper: Mapper) -> None:
    """Check if the given scenario can be mapped.

    Args:
        circuit: Circuit containing the scenario to check against.
        mapper: Mapper to use.
    """
    squirrel_ir_copy = deepcopy(circuit.squirrel_ir)
    circuit.map(mapper)
    assert circuit.squirrel_ir == squirrel_ir_copy, "A Mapper pass should not change the SquirrelIR"
