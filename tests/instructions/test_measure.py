from opensquirrel import Circuit
from opensquirrel.passes.decomposer import McKayDecomposer
from opensquirrel.passes.merger.single_qubit_gates_merger import SingleQubitGatesMerger


def test_measure() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0

        qubit[2] q
        bit[2] b

        b[0, 1] = measure q[0, 1]
        """,
    )
    assert (
        str(circuit)
        == """version 3.0

qubit[2] q
bit[2] b

b[0] = measure q[0]
b[1] = measure q[1]
"""
    )


def test_consecutive_measures() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0

        qubit[3] q
        bit[3] b

        H q[0]
        H q[1]
        H q[2]
        b[0] = measure q[0]
        b[2] = measure q[2]
        b[1] = measure q[1]
        """,
    )
    assert (
        str(circuit)
        == """version 3.0

qubit[3] q
bit[3] b

H q[0]
H q[1]
H q[2]
b[0] = measure q[0]
b[2] = measure q[2]
b[1] = measure q[1]
"""
    )


def test_measures_unrolling() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0

        qubit[6] q
        bit[6] b

        H q[0]
        CNOT q[0], q[1]
        b[1, 4] = measure q[1, 4]
        b[2:5] = measure q[0:3]
        b = measure q
        """,
    )
    assert (
        str(circuit)
        == """version 3.0

qubit[6] q
bit[6] b

H q[0]
CNOT q[0], q[1]
b[1] = measure q[1]
b[4] = measure q[4]
b[2] = measure q[0]
b[3] = measure q[1]
b[4] = measure q[2]
b[5] = measure q[3]
b[0] = measure q[0]
b[1] = measure q[1]
b[2] = measure q[2]
b[3] = measure q[3]
b[4] = measure q[4]
b[5] = measure q[5]
"""
    )


def test_measure_order() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0

        qubit[2] q
        bit[2] b

        Rz(-pi/3) q[0]
        Rz(pi/2) q[1]
        b[1, 0] = measure q[1, 0]
        """,
    )
    circuit.merge(merger=SingleQubitGatesMerger())
    circuit.decompose(decomposer=McKayDecomposer())
    assert (
        str(circuit)
        == """version 3.0

qubit[2] q
bit[2] b

Rz(1.5707963) q[1]
b[1] = measure q[1]
Rz(-1.0471976) q[0]
b[0] = measure q[0]
"""
    )


def test_multiple_qubit_bit_definitions_and_mid_circuit_measure_instructions() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0

        qubit q0
        bit b0
        X q0
        b0 = measure q0

        qubit q1
        bit b1
        H q1
        CNOT q1, q0
        b1 = measure q1
        b0 = measure q0
        """,
        strict = True
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
