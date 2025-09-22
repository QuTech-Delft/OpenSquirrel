"""This module contains checks for the ``Mapper`` pass."""

from __future__ import annotations

from copy import deepcopy

from opensquirrel import I
from opensquirrel.circuit import Circuit
from opensquirrel.ir import IR, Measure
from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGate
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager


def _check_scenario(circuit: Circuit, mapper: Mapper) -> None:
    """Check if the given scenario can be mapped.

    Args:
        circuit: Circuit containing the scenario to check against.
        mapper: Mapper to use.
    """
    ir_copy = deepcopy(circuit.ir)
    circuit.map(mapper)
    assert circuit.ir == ir_copy, "A Mapper pass should not change the IR"


def check_mapper(mapper: Mapper) -> None:
    """Check if the `mapper` complies with the OpenSquirrel requirements.

    If a ``Mapper`` implementation passes these checks, it should be compatible with the ``Circuit.map`` method.

    Args:
        mapper: Mapper to check.
    """
    assert isinstance(mapper, Mapper)

    register_manager = RegisterManager(QubitRegister(10), BitRegister(10))
    ir = IR()
    circuit = Circuit(register_manager, ir)
    _check_scenario(circuit, mapper)

    ir = IR()
    ir.add_gate(BlochSphereRotation(42, (1, 0, 0), 1, 2))
    ir.add_gate(ControlledGate(42, I(100)))
    ir.add_non_unitary(Measure(42, 42, (0, 0, 1)))
    Circuit(register_manager, ir)
    _check_scenario(circuit, mapper)
