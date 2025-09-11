import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.passes.validator import InteractionValidator, PrimitiveGateValidator


class TestInteractionValidator:
    @pytest.fixture
    def connectivity(self) -> dict[str, list[int]]:
        return {"0": [1, 2], "1": [0, 2, 3], "2": [0, 1, 4], "3": [1, 4], "4": [2, 3]}

    @pytest.fixture
    def interaction_validator(self, connectivity: dict[str, list[int]]) -> InteractionValidator:
        return InteractionValidator(connectivity)

    def test_example_1(self, interaction_validator: InteractionValidator) -> None:
        builder = CircuitBuilder(5)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.H(2)
        builder.CNOT(1, 2)
        builder.CNOT(2, 4)
        builder.CNOT(3, 4)
        circuit = builder.to_circuit()
        circuit.validate(validator=interaction_validator)

    def test_example_2(self, interaction_validator: InteractionValidator) -> None:
        builder = CircuitBuilder(5)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.CNOT(0, 3)
        builder.H(2)
        builder.CNOT(1, 2)
        builder.CNOT(1, 3)
        builder.CNOT(2, 3)
        builder.CNOT(3, 4)
        builder.CNOT(0, 4)
        circuit = builder.to_circuit()

        with pytest.raises(
            ValueError,
            match=r"the following qubit interactions in the circuit prevent a 1-to-1"
            r" mapping:\{\(2, 3\), \(0, 3\), \(0, 4\)\}",
        ):
            circuit.validate(validator=interaction_validator)


class TestPrimitiveGateValidator:
    def test_example_1(self) -> None:
        from math import pi

        pgs = ["I", "Rx", "Ry", "Rz", "CZ"]

        builder = CircuitBuilder(5)
        builder.Rx(0, pi / 2)
        builder.Ry(1, -pi / 2)
        builder.CZ(0, 1)
        builder.Ry(1, pi / 2)
        circuit = builder.to_circuit()

        circuit.validate(validator=PrimitiveGateValidator(primitive_gate_set=pgs))

    def test_example_2(self) -> None:
        pgs = ["I", "X90", "mX90", "Y90", "mY90", "Rz", "CZ"]

        builder = CircuitBuilder(5)
        builder.I(0)
        builder.X90(1)
        builder.mX90(2)
        builder.Y90(3)
        builder.mY90(4)
        builder.Rz(0, 2)
        builder.CZ(1, 2)
        builder.H(0)
        builder.CNOT(1, 2)
        circuit = builder.to_circuit()

        with pytest.raises(ValueError, match=r"the following gates are not in the primitive gate set: ['H', 'CNOT']"):
            circuit.validate(validator=PrimitiveGateValidator(primitive_gate_set=pgs))
