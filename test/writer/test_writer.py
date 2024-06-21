from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import CR, H
from opensquirrel.ir import IR, BlochSphereRotation, Comment, Float, Qubit
from opensquirrel.register_manager import QubitRegister, RegisterManager
from opensquirrel.writer import writer


def test_write() -> None:
    register_manager = RegisterManager(QubitRegister(3))
    ir = IR()
    circuit = Circuit(register_manager, ir)

    assert (
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

"""
    )

    ir.add_gate(H(Qubit(0)))
    ir.add_gate(CR(Qubit(0), Qubit(1), Float(1.234)))
    circuit = Circuit(register_manager, ir)

    assert (
        writer.circuit_to_string(circuit)
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
        writer.circuit_to_string(circuit)
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
        writer.circuit_to_string(circuit)
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
        writer.circuit_to_string(circuit)
        == """version 3.0

qubit[3] q

CR(1.6546515) q[0], q[1]
"""
    )
