from opensquirrel import Circuit
from opensquirrel.passes.decomposer import McKayDecomposer
from opensquirrel.passes.merger.single_qubit_gates_merger import SingleQubitGatesMerger


def test_qubit_variable_b_and_bit_variable_q() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0

        qubit[2] b
        bit[2] q
        X b[0]
        q[0] = measure b[0]

        H b[1]
        CNOT b[1], b[00]
        q[1] = measure b[1]
        q[0] = measure b[0]
        """,
        strict=True,
    )
    circuit.merge(merger=SingleQubitGatesMerger())
    circuit.decompose(decomposer=McKayDecomposer())
    assert (
        str(circuit)
        == """version 3.0

qubit[2] q
bit[2] b

X90 q[0]
X90 q[0]
b[0] = measure q[0]
Rz(1.5707963) q[1]
X90 q[1]
Rz(1.5707963) q[1]
CNOT q[1], q[0]
b[1] = measure q[1]
b[0] = measure q[0]
"""
    )
