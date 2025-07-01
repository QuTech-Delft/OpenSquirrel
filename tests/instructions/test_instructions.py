from opensquirrel import Circuit


def test_parse_instructions() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0

        qubit[2] q
        bit[2] b

        // Initialization
        init q

        // Control instructions
        barrier q
        wait(5) q

        // Single-qubit instructions
        I q[0]
        H q[0]
        X q[0]
        X90 q[0]
        mX90 q[0]
        Y q[0]
        Y90 q[0]
        mY90 q[0]
        Z q[0]
        S q[0]
        Sdag q[0]
        T q[0]
        Tdag q[0]
        Rn(1,0,0,pi/2,pi/4) q[0]
        Rx(pi/2) q[0]
        Ry(pi/2) q[0]
        Rz(tau) q[0]

        // Reset instruction
        reset q

        // Measurement instruction (mid-circuit)
        b = measure q

        // Two-qubit instructions
        CNOT q[0], q[1]
        CZ q[0], q[1]
        CR(pi) q[0], q[1]
        CRk(2) q[0], q[1]
        SWAP q[0], q[1]

        // Measurement instruction (final)
        b = measure q
        """,
    )

    assert (
        str(circuit)
        == """version 3.0

qubit[2] q
bit[2] b

init q[0]
init q[1]
barrier q[0]
barrier q[1]
wait(5) q[0]
wait(5) q[1]
I q[0]
H q[0]
X q[0]
X90 q[0]
mX90 q[0]
Y q[0]
Y90 q[0]
mY90 q[0]
Z q[0]
S q[0]
Sdag q[0]
T q[0]
Tdag q[0]
Rn(1.0, 0.0, 0.0, 1.5707963, 0.78539816) q[0]
Rx(1.5707963) q[0]
Ry(1.5707963) q[0]
Rz(6.2831853) q[0]
reset q[0]
reset q[1]
b[0] = measure q[0]
b[1] = measure q[1]
CNOT q[0], q[1]
CZ q[0], q[1]
CR(3.1415927) q[0], q[1]
CRk(2) q[0], q[1]
SWAP q[0], q[1]
b[0] = measure q[0]
b[1] = measure q[1]
"""
    )
