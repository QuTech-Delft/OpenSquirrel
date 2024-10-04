import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.mapper.mapping import Mapping
from opensquirrel.mapper.qubit_remapper import get_remapped_ir, remap_ir


class TestRemapper:
    @pytest.fixture
    def circuit_3(self) -> Circuit:
        builder = CircuitBuilder(3)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.H(2)
        return builder.to_circuit()

    @pytest.fixture
    def circuit_3_remapped(self) -> Circuit:
        builder = CircuitBuilder(3)
        builder.H(2)
        builder.CNOT(2, 1)
        builder.H(0)
        return builder.to_circuit()

    @pytest.fixture
    def circuit_4(self) -> Circuit:
        builder = CircuitBuilder(4)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.X(2)
        builder.Y(3)
        return builder.to_circuit()

    @pytest.fixture
    def circuit_4_remapped(self) -> Circuit:
        builder = CircuitBuilder(4)
        builder.H(3)
        builder.CNOT(3, 1)
        builder.X(0)
        builder.Y(2)
        return builder.to_circuit()

    @pytest.fixture
    def mapping_3(self) -> Mapping:
        return Mapping([2, 1, 0])

    @pytest.fixture
    def mapping_4(self) -> Mapping:
        return Mapping([3, 1, 0, 2])

    def test_get_remapped_ir_raise_value_error(self, circuit_3: Circuit, mapping_4: Mapping) -> None:
        with pytest.raises(ValueError, match="mapping is larger than the qubit register size"):
            get_remapped_ir(circuit_3, mapping_4)

    def test_get_remapped_ir_3_ok(self, circuit_3: Circuit, circuit_3_remapped: Circuit, mapping_3: Mapping) -> None:
        circuit_3.ir = get_remapped_ir(circuit_3, mapping_3)
        assert circuit_3 == circuit_3_remapped

    def test_get_remapped_ir_4_ok(self, circuit_4: Circuit, circuit_4_remapped: Circuit, mapping_4: Mapping) -> None:
        circuit_4.ir = get_remapped_ir(circuit_4, mapping_4)
        assert circuit_4 == circuit_4_remapped

    def test_remap_ir_raise_value_error(self, circuit_3: Circuit, mapping_4: Mapping) -> None:
        with pytest.raises(ValueError, match="mapping is larger than the qubit register size"):
            remap_ir(circuit_3, mapping_4)

    def test_remap_ir_3_ok(self, circuit_3: Circuit, circuit_3_remapped: Circuit, mapping_3: Mapping) -> None:
        remap_ir(circuit_3, mapping_3)
        assert circuit_3 == circuit_3_remapped

    def test_remap_ir_4_ok(self, circuit_4: Circuit, circuit_4_remapped: Circuit, mapping_4: Mapping) -> None:
        remap_ir(circuit_4, mapping_4)
        assert circuit_4 == circuit_4_remapped
