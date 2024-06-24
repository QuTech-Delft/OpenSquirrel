from opensquirrel.circuit import Circuit
from opensquirrel.decomposer.mckay_decomposer import McKayDecomposer
from opensquirrel.default_gates import CR, H
from opensquirrel.ir import IR, BlochSphereRotation, Comment, Float, Qubit
from opensquirrel.register_manager import QubitRegister, RegisterManager
from opensquirrel.writer import cqasm_lite_writer


def test_write() -> None:
    register_manager = RegisterManager(QubitRegister(3))
    ir = IR()
    circuit = Circuit(register_manager, ir)

    assert (
        cqasm_lite_writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

"""
    )

    ir.add_gate(H(Qubit(0)))
    ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
    circuit = Circuit(register_manager, ir)

    assert (
        cqasm_lite_writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

H q[0]
CR(1.234) q[0], q[1]
"""
    )


def test_anonymous_gate() -> None:
    register_manager = RegisterManager(QubitRegister(2))
    ir = IR()
    ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
    ir.add_gate(BlochSphereRotation(Qubit(0), axis=(1, 1, 1), angle=1.23))
    ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
    circuit = Circuit(register_manager, ir)

    assert (
        cqasm_lite_writer.circuit_to_string(circuit)
        == """version 3.0

qubit[2] q

CR(1.234) q[0], q[1]
<anonymous-gate>
CR(1.234) q[0], q[1]
"""
    )


def test_comment() -> None:
    register_manager = RegisterManager(QubitRegister(3))
    ir = IR()
    ir.add_gate(H(Qubit(0)))
    ir.add_comment(Comment("My comment"))
    ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
    circuit = Circuit(register_manager, ir)

    assert (
        cqasm_lite_writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

H q[0]

/* My comment */

CR(1.234) q[0], q[1]
"""
    )


def test_cap_significant_digits() -> None:
    register_manager = RegisterManager(QubitRegister(3))
    ir = IR()
    ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.6546514861321684321654)))
    circuit = Circuit(register_manager, ir)

    assert (
        cqasm_lite_writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

CR(1.6546515) q[0], q[1]
"""
    )


def test_measurement() -> None:
    circuit = Circuit.from_string(
        """
        version 3.0

        qubit[3] q
        bit[3] b

        Ry(2.34) q[2]
        Rz(1.5707963) q[0]
        Ry(-0.2) q[0]
        CNOT q[1], q[0]
        Rz(1.5789) q[0]
        CNOT q[1], q[0]
        Rz(2.5707963) q[1]
        b[0, 2] = measure q[0, 2]
        """,
    )
    circuit.merge_single_qubit_gates()
    circuit.decompose(decomposer=McKayDecomposer())
    assert (
        cqasm_lite_writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

Rz(1.5707963) q[0]
X90 q[0]
Rz(2.9415927) q[0]
X90 q[0]
Rz(3.1415926) q[0]
CNOT q[1], q[0]
Rz(1.5789) q[0]
CNOT q[1], q[0]
measure q[0]
Rz(3.1415927) q[2]
X90 q[2]
Rz(0.80159265) q[2]
X90 q[2]
measure q[2]
Rz(2.5707963) q[1]
"""
    )
