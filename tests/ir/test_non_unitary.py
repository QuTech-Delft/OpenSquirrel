import pytest

from opensquirrel.ir import Bit, Measure, Qubit


class TestMeasure:
    @pytest.fixture
    def measure(self) -> Measure:
        return Measure(42, 42, axis=(0, 0, 1))

    def test_repr(self, measure: Measure) -> None:
        expected_repr = "Measure(qubit=Qubit[42], bit=Bit[42], axis=Axis[0. 0. 1.])"
        assert repr(measure) == expected_repr

    def test_equality(self, measure: Measure) -> None:
        measure_eq = Measure(42, 42, axis=(0, 0, 1))
        assert measure == measure_eq

    @pytest.mark.parametrize(
        "other_measure",
        [Measure(43, 43, axis=(0, 0, 1)), Measure(42, 42, axis=(1, 0, 0)), "test"],
        ids=["qubit", "axis", "type"],
    )
    def test_inequality(self, measure: Measure, other_measure: Measure | str) -> None:
        assert measure != other_measure

    def test_get_bit_operands(self, measure: Measure) -> None:
        assert measure.get_bit_operands() == [Bit(42)]

    def test_get_qubit_operands(self, measure: Measure) -> None:
        assert measure.get_qubit_operands() == [Qubit(42)]
