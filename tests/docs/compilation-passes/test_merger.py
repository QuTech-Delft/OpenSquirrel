from math import pi

from opensquirrel import CircuitBuilder
from opensquirrel.passes.decomposer import McKayDecomposer
from opensquirrel.passes.merger import SingleQubitGatesMerger, TwoQubitGatesMerger


class TestSingleQubitGatesMerger:
    def test_four_rx_to_one_rx(self) -> None:
        builder = CircuitBuilder(1)
        for _ in range(4):
            builder.Rx(0, pi / 4)
        circuit = builder.to_circuit()

        circuit.merge(merger=SingleQubitGatesMerger())

        assert (
            str(circuit)
            == """version 3.0

qubit[1] q

Rx(3.1415927) q[0]
"""
        )

    def test_no_merge_across(self) -> None:
        builder = CircuitBuilder(2, 2)
        builder.Ry(0, pi / 2).X(0).CNOT(0, 1).H(0).X(1).barrier(1).H(0).X(1).measure(0, 0).H(0).X(1)
        circuit = builder.to_circuit()

        circuit.merge(merger=SingleQubitGatesMerger())

        assert (
            str(circuit)
            == """version 3.0

qubit[2] q
bit[2] b

H q[0]
CNOT q[0], q[1]
H q[0]
X q[1]
barrier q[1]
H q[0]
b[0] = measure q[0]
H q[0]
"""
        )

    def test_increase_circuit_depth(self) -> None:
        builder = CircuitBuilder(1)
        builder.Rx(0, pi / 3).Ry(0, pi / 5)
        circuit = builder.to_circuit()

        circuit.merge(merger=SingleQubitGatesMerger())
        circuit.decompose(decomposer=McKayDecomposer())

        assert (
            str(circuit)
            == """version 3.0

qubit[1] q

Rz(-2.2688338) q[0]
X90 q[0]
Rz(1.9872376) q[0]
X90 q[0]
Rz(-1.2436334) q[0]
"""
        )


class TestTwoQubitGatesMerger:
    def test_four_cr_to_one_cz(self) -> None:
        builder = CircuitBuilder(2)
        for _ in range(4):
            builder.CR(0, 1, pi / 4)
        circuit = builder.to_circuit()

        circuit.merge(merger=TwoQubitGatesMerger())

        assert (
            str(circuit)
            == """version 3.0

qubit[2] q

CZ q[0], q[1]
"""
        )

    def test_merge_with_single_qubit_gates(self) -> None:
        builder = CircuitBuilder(2)
        builder.SWAP(0, 1).CZ(0, 1).S(0).S(1)
        circuit = builder.to_circuit()

        circuit.merge(merger=TwoQubitGatesMerger())

        assert (
            str(circuit)
            == """version 3.0

qubit[2] q

ISWAP q[0], q[1]
"""
        )

    def test_greedy_merging(self) -> None:
        builder = CircuitBuilder(3)
        builder.CNOT(0, 1).H(1).CNOT(2, 1).H(1)
        circuit = builder.to_circuit()

        circuit.merge(merger=TwoQubitGatesMerger())

        expected_circuit = (
            "version 3.0\n\nqubit[3] q\n\n"
            "TwoQubitGate(qubits=[(Qubit[0], Qubit[1])], "
            "gate_semantic=MatrixGateSemantic(matrix=[[ 0.70711+0.j  0.70711-0.j  "
            "0.     +0.j  0.     +0.j] [ 0.70711-0.j -0.70711+0.j  0.     +0.j  "
            "0.     +0.j] [ 0.     +0.j  0.     +0.j  0.70711-0.j  0.70711+0.j] "
            "[ 0.     +0.j  0.     +0.j -0.70711+0.j  0.70711-0.j]]))\n"
            "TwoQubitGate(qubits=[(Qubit[1], Qubit[2])], "
            "gate_semantic=MatrixGateSemantic(matrix=[[ 0.70711+0.j  0.     +0.j  "
            "0.70711-0.j  0.     +0.j] [ 0.     +0.j  0.70711-0.j  0.     +0.j  "
            "0.70711+0.j] [ 0.70711-0.j  0.     +0.j -0.70711+0.j  0.     +0.j] "
            "[ 0.     +0.j -0.70711+0.j  0.     +0.j  0.70711-0.j]]))\n"
        )
        assert str(circuit) == expected_circuit
