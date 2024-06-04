import pytest

from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import CNOT, H, X, Y
from opensquirrel.ir import IR, Qubit
from opensquirrel.mapper.mapping import Mapping
from opensquirrel.mapper.qubit_remapper import get_remapped_ir, remap_ir
from opensquirrel.register_manager import RegisterManager


class TestRemapper:
    @pytest.fixture
    def circuit_3(self) -> Circuit:
        ir = IR()
        ir.add_gate(H(Qubit(0)))
        ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        ir.add_gate(H(Qubit(2)))
        return Circuit(RegisterManager(qubit_register_size=3), ir)

    @pytest.fixture
    def circuit_3_remapped(self) -> Circuit:
        ir = IR()
        ir.add_gate(H(Qubit(2)))
        ir.add_gate(CNOT(Qubit(2), Qubit(1)))
        ir.add_gate(H(Qubit(0)))
        return Circuit(RegisterManager(qubit_register_size=3), ir)

    @pytest.fixture
    def circuit_4(self) -> Circuit:
        ir = IR()
        ir.add_gate(H(Qubit(0)))
        ir.add_gate(CNOT(Qubit(0), Qubit(1)))
        ir.add_gate(X(Qubit(2)))
        ir.add_gate(Y(Qubit(3)))
        return Circuit(RegisterManager(qubit_register_size=4), ir)

    @pytest.fixture
    def circuit_4_remapped(self) -> Circuit:
        ir = IR()
        ir.add_gate(H(Qubit(3)))
        ir.add_gate(CNOT(Qubit(3), Qubit(1)))
        ir.add_gate(X(Qubit(0)))
        ir.add_gate(Y(Qubit(2)))
        return Circuit(RegisterManager(qubit_register_size=4), ir)

    @pytest.fixture
    def mapping_3(self) -> Mapping:
        return Mapping([2, 1, 0])

    @pytest.fixture
    def mapping_4(self) -> Mapping:
        return Mapping([3, 1, 0, 2])

    def test_get_remapped_ir_raise_assert(self, circuit_3: Circuit, mapping_4: Mapping) -> None:
        with pytest.raises(AssertionError):
            get_remapped_ir(circuit_3, mapping_4)

    def test_get_remapped_ir_3_ok(self, circuit_3: Circuit, circuit_3_remapped: Circuit, mapping_3: Mapping) -> None:
        circuit_3.ir = get_remapped_ir(circuit_3, mapping_3)
        assert circuit_3 == circuit_3_remapped

    def test_get_remapped_ir_4_ok(self, circuit_4: Circuit, circuit_4_remapped: Circuit, mapping_4: Mapping) -> None:
        circuit_4.ir = get_remapped_ir(circuit_4, mapping_4)
        assert circuit_4 == circuit_4_remapped

    def test_remap_ir_raise_assert(self, circuit_3: Circuit, mapping_4: Mapping) -> None:
        with pytest.raises(AssertionError):
            remap_ir(circuit_3, mapping_4)

    def test_remap_ir_3_ok(self, circuit_3: Circuit, circuit_3_remapped: Circuit, mapping_3: Mapping) -> None:
        remap_ir(circuit_3, mapping_3)
        assert circuit_3 == circuit_3_remapped

    def test_remap_ir_4_ok(self, circuit_4: Circuit, circuit_4_remapped: Circuit, mapping_4: Mapping) -> None:
        remap_ir(circuit_4, mapping_4)
        assert circuit_4 == circuit_4_remapped
