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
Ry(1.234) q[1]
CNOT q[0], q[1]
CR(5.123) q[1], q[0]
CRk(23) q[0], q[1]
""",
    )

    assert circuit.qubit_register_size == 2
    assert circuit.qubit_register_name == "q"
    assert circuit.ir.statements == [
        H(0),
        I(0),
        Ry(1, Float(1.234)),
        CNOT(0, 1),
        CR(1, 0, Float(5.123)),
        CRk(0, 1, 23),
    ]


def test_sgmq(parser: Parser) -> None:
    circuit = parser.circuit_from_string(
        """
version 3.0

qubit[20] q

H q[5:9]
X q[13,17]
CRk(23) q[0, 3], q[1, 4]
""",
    )

    assert circuit.qubit_register_size == 20
    assert circuit.qubit_register_name == "q"
    assert circuit.ir.statements == [
        H(5),
        H(6),
        H(7),
        H(8),
        H(9),
        X(13),
        X(17),
        CRk(0, 1, 23),
        CRk(3, 4, 23),
    ]


def test_error(parser: Parser) -> None:
    with pytest.raises(
        IOError,
        match="Error at <unknown file name>:1:30..31: failed to resolve variable 'q'",
    ):
        parser.circuit_from_string("version 3.0; qubit[20] qu; H q[5]")


@pytest.mark.parametrize(
    ("circuit_string", "expected_output"),
    [
        (
            "version 3.0\nqubit q\n",
            "version 3.0\n\nqubit[1] q\n",
        ),
        (
            "version 3.0\nqubit q\nbit b\n",
            "version 3.0\n\nqubit[1] q\nbit[1] b\n",
        ),
        (
            "version 3.0\nbit b\n",
            "version 3.0\n\nbit[1] b\n",
        ),
        (
            "version 3.0",
            "version 3.0\n",
        ),
        (
            "version 3.0; qubit q",
            "version 3.0\n\nqubit[1] q\n",
        ),
        (
            "version 3.0; qubit q; bit b",
            "version 3.0\n\nqubit[1] q\nbit[1] b\n",
        ),
        (
            "version 3.0; bit b",
            "version 3.0\n\nbit[1] b\n",
        ),
    ],
    ids=[
        "only_qubit",
        "qubit_and_bit",
        "only_bit",
        "empty_declaration",
        "semicolon_qubit",
        "semicolon_qubit_and_bit",
        "semicolon_bit",
    ],
)
def test_simplest(parser: Parser, circuit_string: str, expected_output: str) -> None:
    circuit = parser.circuit_from_string(circuit_string)
    assert str(circuit) == expected_output


@pytest.mark.parametrize(
    ("circuit_string", "expected_result"),
    [
        (
            "version 3.0; qubit q; inv.X q",
            [BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=math.pi * -1, phase=math.pi / 2)],
        ),
        (
            "version 3.0; qubit q; pow(2).Rx(pi) q",
            [BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=math.pi * 2, phase=0)],
        ),
        (
            "version 3.0; qubit q; pow(2).inv.X q",
            [BlochSphereRotation(qubit=0, axis=(1, 0, 0), angle=math.pi * -2, phase=math.pi / 2)],
        ),
        (
            "version 3.0; qubit[2] q; ctrl.pow(2).inv.X q[0], q[1]",
            [ControlledGate(0, BlochSphereRotation(qubit=1, axis=(1, 0, 0), angle=math.pi * -2, phase=math.pi / 2))],
        ),
    ],
    ids=["inv", "pow_2_Rx", "pow_2_inv", "ctrl_pow_2_inv"],
)
def test_gate_modifiers(parser: Parser, circuit_string: str, expected_result: list[Gate]) -> None:
    circuit = parser.circuit_from_string(circuit_string)
    assert circuit.ir.statements == expected_result
