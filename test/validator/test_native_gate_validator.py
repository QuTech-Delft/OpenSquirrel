# Tests for native gate checker pass

import math

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.ir import Float
from opensquirrel.passes.validator.native_gate_validator import NativeGateValidator


@pytest.fixture(name="validator")
def validator_fixture() -> NativeGateValidator:
    native_gate_set = ["H", "Z", "Y", "Rx", "CNOT"]
    return NativeGateValidator(native_gate_set)


@pytest.fixture
def circuit_with_3_cnot() -> Circuit:
    builder = CircuitBuilder(5)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.H(2)
    builder.CNOT(1, 2)
    builder.CNOT(2, 4)
    builder.Z(2)
    builder.Y(1)
    builder.Rx(0, Float(math.pi / 3))
    return builder.to_circuit()


@pytest.fixture
def circuit_with_4_cnot() -> Circuit:
    builder = CircuitBuilder(5)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.CNOT(0, 3)
    builder.H(2)
    builder.CNOT(1, 2)
    builder.SWAP(1, 3)
    builder.Ry(2, Float(math.pi / 3))
    return builder.to_circuit()


def test_matching_gates(validator: NativeGateValidator, circuit_with_3_cnot: Circuit) -> None:
    try:
        validator.validate(circuit_with_3_cnot.ir)
    except ValueError:
        pytest.fail("check() raised ValueError unexpectedly")


def test_non_matching_gates(validator: NativeGateValidator, circuit_with_4_cnot: Circuit) -> None:
    with pytest.raises(ValueError, match="The following gates are not in the native gate set:.*"):
        validator.validate(circuit_with_4_cnot.ir)
