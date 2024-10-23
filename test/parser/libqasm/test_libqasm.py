import math
import pytest

from opensquirrel.default_gates import CNOT, CR, CRk, H, I, Ry, X, default_gate_aliases, default_gate_set
from opensquirrel.ir import BlochSphereRotation, ControlledGate, Float, Gate
from opensquirrel.parser.libqasm.parser import Parser


@pytest.fixture(name="parser")
def parser_fixture() -> Parser:
    return Parser(gate_set=default_gate_set, gate_aliases=default_gate_aliases)


def test_simple(parser: Parser) -> None:
    circuit = parser.circuit_from_string(
        """
version 3.0

qubit[2] q

H q[0]
I q[0]
Ry q[1], 1.234
CNOT q[0], q[1]
CR q[1], q[0], 5.123
CRk q[0], q[1], 23
""",
    )

    assert circuit.qubit_register_size == 2
    assert circuit.qubit_register_name == "q"
    assert circuit.ir.statements == [H(0), I(0), Ry(1, Float(1.234)), CNOT(0, 1), CR(1, 0, Float(5.123)), CRk(0, 1, 23)]


def test_sgmq(parser: Parser) -> None:
    circuit = parser.circuit_from_string(
        """
version 3.0

qubit[20] q

H q[5:9]
X q[13,17]
CRk q[0, 3], q[1, 4], 23
""",
    )

    assert circuit.qubit_register_size == 20
    assert circuit.qubit_register_name == "q"
    assert circuit.ir.statements == [H(5), H(6), H(7), H(8), H(9), X(13), X(17), CRk(0, 1, 23), CRk(3, 4, 23)]


def test_error(parser: Parser) -> None:
    with pytest.raises(IOError, match="Error at <unknown file name>:1:30..31: failed to resolve variable 'q'"):
        parser.circuit_from_string("version 3.0; qubit[20] qu; H q[5]")


@pytest.mark.parametrize(
    ("error_message", "circuit_string"),
    [
        (
            r"parsing error: Error at <unknown file name>:1:26\.\.27: "
            r"failed to resolve instruction 'H' with argument pack \(qubit, int\)",
            "version 3.0; qubit[1] q; H q[0], 1",
        ),
        (
            r"parsing error: Error at <unknown file name>:1:26\.\.30: "
            r"failed to resolve instruction 'CNOT' with argument pack \(qubit, int\)",
            "version 3.0; qubit[1] q; CNOT q[0], 1",
        ),
        (
            r"parsing error: Error at <unknown file name>:1:26\.\.28: "
            r"failed to resolve instruction 'Ry' with argument pack \(qubit, float, int\)",
            "version 3.0; qubit[3] q; Ry q[0], 1.23, 1",
        ),
    ],
    ids=["H[q,i]", "CNOT[q,i]", "Ry[q,f,i]"],
)
def test_wrong_gate_argument_number_or_types(parser: Parser, error_message: str, circuit_string: str) -> None:
    with pytest.raises(IOError, match=error_message):
        parser.circuit_from_string(circuit_string)


@pytest.mark.parametrize(
    ("circuit_string", "expected_result"),
    [
        ("version 3.0; qubit q; inv.X q",
         [BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=math.pi * -1, phase=math.pi / 2)]),
        ("version 3.0; qubit q; pow(2).X q",
         [BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=math.pi * 2, phase=math.pi / 2)]),
        ("version 3.0; qubit q; pow(2).inv.X q",
         [BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=math.pi * -2, phase=math.pi / 2)]),
        ("version 3.0; qubit[2] q; ctrl.pow(2).inv.X q[0], q[1]",
         [ControlledGate(0,
                         BlochSphereRotation(qubit=1, axis=(1, 0, 0), angle=math.pi * -2, phase=math.pi / 2))]),
    ],
    ids=["inv", "pow_2", "pow_2_inv", "ctrl_pow_2_inv"],
)
def test_gate_modifiers(parser: Parser, circuit_string: str, expected_result: list[Gate]) -> None:
    circuit = parser.circuit_from_string(circuit_string)
    assert circuit.ir.statements == expected_result
