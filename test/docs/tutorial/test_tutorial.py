import importlib.util
import math

import numpy as np
import pytest
import quantify_scheduler

from opensquirrel import CNOT, CZ, Circuit, CircuitBuilder, H, Ry, Rz
from opensquirrel.ir import BlochSphereRotation, ControlledGate, MatrixGate, QubitLike
from opensquirrel.passes.decomposer import ZYZDecomposer, McKayDecomposer
from opensquirrel.passes.exporter import ExportFormat
from opensquirrel.passes.merger import SingleQubitGatesMerger


class TestTutorial:

    @pytest.fixture
    def circuit(self) -> Circuit:
        builder = CircuitBuilder(1)
        builder.H(0)
        return builder.to_circuit()

    def test_apply_mckay_decomposer(self, circuit: Circuit) -> None:
        circuit.decompose(decomposer=McKayDecomposer())
        assert str(circuit) == """version 3.0\n\nqubit[1] q\n\nRz(1.5707963) q[0]\nX90 q[0]\nRz(1.5707963) q[0]\n"""

    def test_export_to_qs_schedule(self, circuit: Circuit) -> None:
        circuit.decompose(decomposer=McKayDecomposer())
        if importlib.util.find_spec("quantify_scheduler") is None:
            with pytest.raises(
                Exception,
                match="quantify-scheduler is not installed, or cannot be installed on your system",
            ):
                circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        else:
            exported_schedule, _ = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
            assert isinstance(exported_schedule, quantify_scheduler.Schedule)


class TestCreatingACircuit:

    def test_from_a_cqasm_string(self) -> None:
        circuit = Circuit.from_string(
            """
            // Version statement
            version 3.0

            // Qubit register declaration
            qubit[5] q

            // Bit register declaration
            bit[2] b

            // Qubit register initialization
            init q[0, 1]

            // Single-qubit gate
            H q[0]

            // Two-qubit gate
            CNOT q[0], q[1]

            // Control instruction
            barrier q[0, 1]

            // Measure instruction
            b[0, 1] = measure q[0, 1]

            """
        )

        assert (
            str(circuit)
            == """version 3.0

qubit[5] q
bit[2] b

init q[0]
init q[1]
H q[0]
CNOT q[0], q[1]
barrier q[0]
barrier q[1]
b[0] = measure q[0]
b[1] = measure q[1]
"""
        )

    def test_by_using_the_circuit_builder(self) -> None:

        builder = CircuitBuilder(qubit_register_size=5, bit_register_size=2)
        builder.init(0).init(1)
        builder.H(0)
        builder.CNOT(0, 1)
        builder.barrier(0).barrier(1)
        builder.measure(0, 0).measure(1, 1)
        circuit = builder.to_circuit()

        assert (
            str(circuit)
            == """version 3.0

qubit[5] q
bit[2] b

init q[0]
init q[1]
H q[0]
CNOT q[0], q[1]
barrier q[0]
barrier q[1]
b[0] = measure q[0]
b[1] = measure q[1]
"""
        )

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

    connectivity = {
        "0": [1],
        "1": [0, 2],
        "2": [1]
    }

    pgs = ["I", "X", "Z", "X90", "mX90", "S", "Sdag", "T", "Tdag", "Rx", "Rz", "CZ"]

    def test_input_program(self) -> None:

        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[3] q
            bit[2] b

            init q

            Ry(pi / 2) q[0]
            X q[0]
            CNOT q[0], q[2]

            barrier q

            b[0, 1] = measure q[0, 2]
            """
        )

        assert (
            str(circuit)
            == """version 3.0

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

    def test_routing(self) -> None:
        circuit = Circuit.from_string(
            """
            version 3.0

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
        from opensquirrel.passes.router import ShortestPathRouter

        circuit.route(router=ShortestPathRouter(connectivity=self.connectivity))

        print(circuit)
    #     assert (
    #         str(circuit)
    #         == """version 3.0
    #
    # qubit[3] q
    #
    # X q[0]
    # X q[1]
    # X q[2]
    # H q[1]
    # CZ q[0], q[1]
    # H q[1]
    # Ry(6.78) q[2]
    # """
    #     )

    def test_error_predefined_decomposition(self) -> None:
        qc = Circuit.from_string(
            """
            version 3.0
            qubit[3] q

            X q[0:2]
            CNOT q[0], q[1]
            Ry(6.78) q[2]
            """
        )
        with pytest.raises(ValueError, match=r"replacement for gate .*") as e_info:
            qc.replace(CNOT, lambda control_qubit, target_qubit: [H(target_qubit), CZ(control_qubit, target_qubit)])

        assert str(e_info.value) == "replacement for gate CNOT does not preserve the quantum state"

    def test_zyz_decomposer(self) -> None:
        builder = CircuitBuilder(qubit_register_size=1)
        builder.H(0).Z(0).Y(0).Rx(0, math.pi / 3)
        qc = builder.to_circuit()

        qc.decompose(decomposer=ZYZDecomposer())

        assert (
            str(qc)
            == """version 3.0

    qubit[1] q

    Rz(3.1415927) q[0]
    Ry(1.5707963) q[0]
    Rz(3.1415927) q[0]
    Ry(3.1415927) q[0]
    Rz(1.5707963) q[0]
    Ry(1.0471976) q[0]
    Rz(-1.5707963) q[0]
    """
        )

        assert ZYZDecomposer().decompose(H(0)) == [Rz(0, math.pi), Ry(0, math.pi / 2)]


def test_merger() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Ry(1.5707963) q[0]
    X q[0]
    Ry(-1.5707963) q[2]
    CZ q[1], q[2]
    Ry(1.5707963) q[2]
    Ry(-1.5707963) q[1]
    CZ q[2], q[1]
    Ry(1.5707963) q[1]
    Ry(-1.5707963) q[2]
    CZ q[1], q[2]
    Ry(1.5707963) q[2]
    Ry(-1.5707963) q[1]
    CZ q[0], q[1]
    Ry(1.5707963) q[1]
    barrier q[0]
    barrier q[2]
    barrier q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]
        """
    )

    circuit.merge(merger=SingleQubitGatesMerger())

    print(circuit)


def test_mckay() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0

    qubit[3] q
    bit[2] b

    init q[0]
    init q[1]
    init q[2]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[2]
    CZ q[1], q[2]
    Ry(1.5707963) q[2]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[1]
    CZ q[2], q[1]
    Ry(1.5707963) q[1]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[2]
    CZ q[1], q[2]
    H q[0]
    Rn(0.0, -1.0, 0.0, 1.5707963, 0.0) q[1]
    CZ q[0], q[1]
    Ry(1.5707963) q[1]
    Ry(1.5707963) q[2]
    barrier q[0]
    barrier q[2]
    barrier q[1]
    b[0] = measure q[0]
    b[1] = measure q[1]
        """
    )

    circuit.decompose(decomposer=McKayDecomposer())

    print(circuit)
