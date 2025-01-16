# Tests for native gate checker pass

import math

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.ir import Float
from opensquirrel.passes.checker.native_gate_checker import NativeGateChecker


@pytest.fixture(name="checker")
def checker_fixture() -> NativeGateChecker:
    native_gate_set = ["H", "Z", "Y", "Rx", "CNOT"]
    return NativeGateChecker(native_gate_set)


@pytest.fixture
def circuit1() -> Circuit:
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
def circuit2() -> Circuit:
    builder = CircuitBuilder(5)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.CNOT(0, 3)
    builder.H(2)
    builder.CNOT(1, 2)
    builder.SWAP(1, 3)
    builder.Ry(2, Float(math.pi / 3))
    return builder.to_circuit()


def test_matching_gates(checker: NativeGateChecker, circuit1: Circuit) -> None:
    try:
        checker.check(circuit1.ir)
    except ValueError:
        pytest.fail("check() raised ValueError unexpectedly")


def test_non_matching_gates(checker: NativeGateChecker, circuit2: Circuit) -> None:
    with pytest.raises(ValueError, match="The following gates are not in the native gate set:.*"):
        checker.check(circuit2.ir)
