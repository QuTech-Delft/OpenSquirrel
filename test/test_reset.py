from opensquirrel import Circuit, CircuitBuilder


def test_reset() -> None:
    qc = Circuit.from_string(
        """
        version 3.0

        qubit[2] q
        bit[2] b
        H q[0]
        CNOT q[0], q[1]

        reset q[0]
        b = measure q
        """,
    )
    assert (
        str(qc)
        == """version 3.0

qubit[2] q
bit[2] b

H q[0]
CNOT q[0], q[1]
reset q[0]
b[0] = measure q[0]
b[1] = measure q[1]
"""
    )


def test_reset_sgmq() -> None:
    qc = Circuit.from_string(
        """
        version 3.0

        qubit[4] q

        H q[0]
        H q[1:2]
        reset q[2:3]
        H q[3]
        reset q[0:1]
        """,
    )
    assert (
        str(qc)
        == """version 3.0

qubit[4] q

H q[0]
H q[1]
H q[2]
reset q[2]
reset q[3]
H q[3]
reset q[0]
reset q[1]
"""
    )


def test_reset_in_circuit_builder() -> None:
    builder = CircuitBuilder(2, 2)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.reset(0)
    builder.measure(0, 0)
    builder.measure(1, 1)

    qc = builder.to_circuit()

    assert (
        str(qc)
        == """version 3.0

qubit[2] q
bit[2] b

H q[0]
CNOT q[0], q[1]
reset q[0]
b[0] = measure q[0]
b[1] = measure q[1]
"""
    )
