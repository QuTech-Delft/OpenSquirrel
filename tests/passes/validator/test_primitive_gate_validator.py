# Tests for primitive gate validator pass
import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.validator import PrimitiveGateValidator


@pytest.fixture
def validator() -> PrimitiveGateValidator:
    primitive_gate_set = ["I", "U", "X90", "mX90", "Y90", "mY90", "Rz", "CZ"]
    return PrimitiveGateValidator(primitive_gate_set)


@pytest.fixture
def circuit_with_matching_gate_set() -> Circuit:
    builder = CircuitBuilder(5)
    builder.I(0)
    builder.U(0, 1, 2, 3)
    builder.X90(1)
    builder.mX90(2)
    builder.Y90(3)
    builder.mY90(4)
    builder.Rz(0, 2)
    builder.CZ(1, 2)
    return builder.to_circuit()


@pytest.fixture
def circuit_with_unmatching_gate_set() -> Circuit:
    builder = CircuitBuilder(5)
    builder.I(0)
    builder.U(0, 1, 2, 3)
    builder.X90(1)
    builder.mX90(2)
    builder.Y90(3)
    builder.mY90(4)
    builder.Rz(0, 2)
    builder.CZ(1, 2)
    builder.H(0)
    builder.CNOT(1, 2)
    return builder.to_circuit()


def test_matching_gates(validator: PrimitiveGateValidator, circuit_with_matching_gate_set: Circuit) -> None:
    try:
        validator.validate(circuit_with_matching_gate_set.ir)
    except ValueError:
        pytest.fail("validate() raised ValueError unexpectedly")


def test_non_matching_gates(validator: PrimitiveGateValidator, circuit_with_unmatching_gate_set: Circuit) -> None:
    with pytest.raises(ValueError, match=r"the following gates are not in the primitive gate set:.*"):
        validator.validate(circuit_with_unmatching_gate_set.ir)
