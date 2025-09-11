from math import pi

from opensquirrel import CircuitBuilder
from opensquirrel.passes.decomposer import McKayDecomposer
from opensquirrel.passes.merger import SingleQubitGatesMerger


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
