"""This module contains checks for the ``Mapper`` pass."""

from __future__ import annotations

from copy import deepcopy
from typing import OrderedDict

from opensquirrel.circuit import Circuit
from opensquirrel.ir import IR, Measure
from opensquirrel.ir.default_gates import I
from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.register_manager import (
    BIT_REGISTER_NAME,
    QUBIT_REGISTER_NAME,
    BitRegister,
    QubitRegister,
    RegisterManager,
)


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

    register_manager = RegisterManager(
        OrderedDict({QUBIT_REGISTER_NAME: QubitRegister(10)}),
        OrderedDict({BIT_REGISTER_NAME: BitRegister(10)})
    )
    ir = IR()
    circuit = Circuit(register_manager, ir)
    _check_scenario(circuit, mapper)

    ir = IR()
    ir.add_gate(SingleQubitGate(qubit=42, gate_semantic=BlochSphereRotation((1, 0, 0), 1, 2)))
    ir.add_gate(TwoQubitGate(42, 100, gate_semantic=ControlledGateSemantic(I(100))))
    ir.add_non_unitary(Measure(42, 42, (0, 0, 1)))
    Circuit(register_manager, ir)
    _check_scenario(circuit, mapper)
