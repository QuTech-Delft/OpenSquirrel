import importlib.util
import math
from typing import ClassVar

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.passes.decomposer import CNOT2CZDecomposer, McKayDecomposer, SWAP2CZDecomposer
from opensquirrel.passes.exporter import ExportFormat
from opensquirrel.passes.merger import SingleQubitGatesMerger
from opensquirrel.passes.validator import PrimitiveGateValidator, RoutingValidator


@pytest.fixture
def circuit_1() -> Circuit:
    return Circuit.from_string(
        """version 3.0

qubit[3] q
bit[2] b

init q[0]
init q[1]
init q[2]
Ry(1.5707963) q[0]
X q[0]
CNOT q[0], q[2]
barrier q[0]
barrier q[1]
barrier q[2]
b[0] = measure q[0]
b[1] = measure q[2]
"""
    )


@pytest.fixture
def circuit_2() -> Circuit:
    return Circuit.from_string(
        """version 3.0

qubit[3] q
bit[2] b

init q[0]
init q[1]
init q[2]
Ry(1.5707963) q[0]
X q[0]
SWAP q[0], q[1]
CNOT q[1], q[2]
barrier q[1]
barrier q[0]
barrier q[2]
b[0] = measure q[1]
b[1] = measure q[2]
"""
    )


@pytest.fixture
def circuit_3() -> Circuit:
    return Circuit.from_string(
        """version 3.0

qubit[3] q
bit[2] b

init q[0]
init q[1]
init q[2]
Ry(1.5707963) q[0]
X q[0]
Ry(-1.5707963) q[1]
CZ q[0], q[1]
Ry(1.5707963) q[1]
Ry(-1.5707963) q[0]
CZ q[1], q[0]
Ry(1.5707963) q[0]
Ry(-1.5707963) q[1]
CZ q[0], q[1]
Ry(1.5707963) q[1]
CNOT q[1], q[2]
barrier q[1]
barrier q[0]
barrier q[2]
b[0] = measure q[1]
b[1] = measure q[2]
"""
    )


@pytest.fixture
def circuit_4() -> Circuit:
    return Circuit.from_string(
        """version 3.0

qubit[3] q
bit[2] b

init q[0]
init q[1]
init q[2]
Ry(1.5707963) q[0]
X q[0]
Ry(-1.5707963) q[1]
CZ q[0], q[1]
Ry(1.5707963) q[1]
Ry(-1.5707963) q[0]
CZ q[1], q[0]
Ry(1.5707963) q[0]
Ry(-1.5707963) q[1]
CZ q[0], q[1]
Ry(1.5707963) q[1]
Ry(-1.5707963) q[2]
CZ q[1], q[2]
Ry(1.5707963) q[2]
barrier q[1]
barrier q[0]
barrier q[2]
b[0] = measure q[1]
b[1] = measure q[2]
"""
    )


@pytest.fixture
def circuit_5() -> Circuit:
    return Circuit.from_string(
        """version 3.0

qubit[3] q
bit[2] b

init q[0]
init q[1]
init q[2]
H q[0]
Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[1]
CZ q[0], q[1]
Ry(1.5707963) q[1]
Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[0]
CZ q[1], q[0]
Ry(1.5707963) q[0]
Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[1]
CZ q[0], q[1]
Ry(1.5707963) q[1]
Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[2]
CZ q[1], q[2]
Ry(1.5707963) q[2]
barrier q[1]
barrier q[0]
barrier q[2]
b[0] = measure q[1]
b[1] = measure q[2]
"""
    )


@pytest.fixture
def circuit_6() -> Circuit:
    return Circuit.from_string(
        """version 3.0

qubit[3] q
bit[2] b

init q[0]
init q[1]
init q[2]
Rz(1.5707963) q[0]
X90 q[0]
Rz(1.5707963) q[0]
Rz(1.5707963) q[1]
X90 q[1]
Rz(-1.5707963) q[1]
CZ q[0], q[1]
Rz(-1.5707963) q[1]
X90 q[1]
Rz(1.5707963) q[1]
Rz(1.5707963) q[0]
X90 q[0]
Rz(-1.5707963) q[0]
CZ q[1], q[0]
Rz(-1.5707963) q[0]
X90 q[0]
Rz(1.5707963) q[0]
Rz(1.5707963) q[1]
X90 q[1]
Rz(-1.5707963) q[1]
CZ q[0], q[1]
Rz(-1.5707963) q[1]
X90 q[1]
Rz(1.5707963) q[1]
Rz(1.5707963) q[2]
X90 q[2]
Rz(-1.5707963) q[2]
CZ q[1], q[2]
Rz(-1.5707963) q[2]
X90 q[2]
Rz(1.5707963) q[2]
barrier q[1]
barrier q[0]
barrier q[2]
b[0] = measure q[1]
b[1] = measure q[2]
"""
    )


class TestTutorial:
    @pytest.fixture
    def circuit(self) -> Circuit:
        builder = CircuitBuilder(1)
        builder.H(0)
        return builder.to_circuit()

    def test_apply_mckay_decomposer(self, circuit: Circuit) -> None:
        circuit.decompose(decomposer=McKayDecomposer())
        assert str(circuit) == """version 3.0\n\nqubit[1] q\n\nRz(1.5707963) q[0]\nX90 q[0]\nRz(1.5707963) q[0]\n"""


class TestCreatingACircuit:
    def test_from_a_cqasm_string(self, circuit_1: Circuit) -> None:
        circuit = Circuit.from_string(
            """
            // Version statement
            version 3.0

            // Qubit register declaration
            qubit[3] q

            // Bit register declaration
            bit[2] b

            // Qubit register initialization (with SGMQ notation)
            init q

            // Single-qubit gates
            Ry(pi / 2) q[0]
            X q[0]

            // Two-qubit gate
            CNOT q[0], q[2]

            // Control instruction (with SGMQ notation)
            barrier q

            // Measure instruction (with SGMQ notation)
            b[0, 1] = measure q[0, 2]
            """
        )
        assert str(circuit) == str(circuit_1)

    def test_by_using_the_circuit_builder(self, circuit_1: Circuit) -> None:
        builder = CircuitBuilder(qubit_register_size=3, bit_register_size=2)
        builder.init(0).init(1).init(2)
        builder.Ry(0, math.pi / 2)
        builder.X(0)
        builder.CNOT(0, 2)
        builder.barrier(0).barrier(1).barrier(2)
        builder.measure(0, 0).measure(2, 1)
        circuit = builder.to_circuit()

        assert str(circuit) == str(circuit_1)

    def test_circuit_builder_loop(self) -> None:
        qreg_size = 10
        builder = CircuitBuilder(qubit_register_size=qreg_size)
        for qubit_index in range(0, qreg_size, 2):
            builder.H(qubit_index)
        circuit = builder.to_circuit()

        assert (
            str(circuit)
            == """version 3.0

qubit[10] q

H q[0]
H q[2]
H q[4]
H q[6]
H q[8]
"""
        )

    def test_circuit_builder_qft(self) -> None:
        qreg_size = 5
        builder = CircuitBuilder(qubit_register_size=qreg_size)
        for qubit_index in range(qreg_size):
            builder.H(qubit_index)
            for control_index in range(qubit_index + 1, qreg_size):
                target_index = qubit_index
                k = control_index - target_index + 1
                builder.CRk(control_index, target_index, k)
        circuit_qft = builder.to_circuit()
        assert (
            str(circuit_qft)
            == """version 3.0

qubit[5] q

H q[0]
CRk(2) q[1], q[0]
CRk(3) q[2], q[0]
CRk(4) q[3], q[0]
CRk(5) q[4], q[0]
H q[1]
CRk(2) q[2], q[1]
CRk(3) q[3], q[1]
CRk(4) q[4], q[1]
H q[2]
CRk(2) q[3], q[2]
CRk(3) q[4], q[2]
H q[3]
CRk(2) q[4], q[3]
H q[4]
"""
        )


class TestApplyingCompilationPasses:
    connectivity: ClassVar[dict[str, list[int]]] = {"0": [1], "1": [0, 2], "2": [1]}
    pgs: ClassVar[list[str]] = ["I", "X90", "Rx", "Rz", "CZ", "init", "barrier", "measure"]

    def test_routing(self, circuit_1: Circuit, circuit_2: Circuit) -> None:
        circuit = circuit_1
        from opensquirrel.passes.router import ShortestPathRouter

        circuit.route(router=ShortestPathRouter(connectivity=self.connectivity))

        # After a bug-fix CQT-388, the assert can be uncommented.
        # assert str(circuit) == str(circuit_2)                     # noqa

    def test_decomposition_predefined(self, circuit_2: Circuit, circuit_3: Circuit, circuit_4: Circuit) -> None:
        circuit = circuit_2
        circuit.decompose(decomposer=SWAP2CZDecomposer())
        assert str(circuit) == str(circuit_3)

        circuit = circuit_3
        circuit.decompose(decomposer=CNOT2CZDecomposer())
        assert str(circuit) == str(circuit_4)

    def test_merging(self, circuit_4: Circuit, circuit_5: Circuit) -> None:
        circuit = circuit_4
        circuit.merge(merger=SingleQubitGatesMerger())
        assert str(circuit) == str(circuit_5)

    def test_decomposition_inferred(self, circuit_5: Circuit, circuit_6: Circuit) -> None:
        circuit = circuit_5
        circuit.decompose(decomposer=McKayDecomposer())
        assert str(circuit) == str(circuit_6)

    def test_validation(self, circuit_6: Circuit) -> None:
        circuit_6.validate(validator=RoutingValidator(connectivity=self.connectivity))
        circuit_6.validate(validator=PrimitiveGateValidator(primitive_gate_set=self.pgs))


class TestWritingOutAndExporting:
    def test_exporting_to_cqasm_v1(self, circuit_6: Circuit) -> None:
        circuit = circuit_6
        exported_circuit = circuit.export(fmt=ExportFormat.CQASM_V1)

        assert (
            str(exported_circuit)
            == """version 1.0

qubits 3

prep_z q[0]
prep_z q[1]
prep_z q[2]
rz q[0], 1.5707963
x90 q[0]
rz q[0], 1.5707963
rz q[1], 1.5707963
x90 q[1]
rz q[1], -1.5707963
cz q[0], q[1]
rz q[1], -1.5707963
x90 q[1]
rz q[1], 1.5707963
rz q[0], 1.5707963
x90 q[0]
rz q[0], -1.5707963
cz q[1], q[0]
rz q[0], -1.5707963
x90 q[0]
rz q[0], 1.5707963
rz q[1], 1.5707963
x90 q[1]
rz q[1], -1.5707963
cz q[0], q[1]
rz q[1], -1.5707963
x90 q[1]
rz q[1], 1.5707963
rz q[2], 1.5707963
x90 q[2]
rz q[2], -1.5707963
cz q[1], q[2]
rz q[2], -1.5707963
x90 q[2]
rz q[2], 1.5707963
barrier q[1, 0, 2]
measure_z q[1]
measure_z q[2]
"""
        )
