import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.ir import Reset


@pytest.mark.parametrize(
    ("cqasm_string", "expected_result"),
    [
        ("version 3.0; qubit[2] q; reset q[1]; reset q[0]", "version 3.0\n\nqubit[2] q\n\nreset q[1]\nreset q[0]\n"),
        (
            "version 3.0; qubit[4] q; reset q[2:3]; reset q[1, 0]",
            "version 3.0\n\nqubit[4] q\n\nreset q[2]\nreset q[3]\nreset q[1]\nreset q[0]\n",
        ),
    ],
    ids=["reset", "reset sgmq"],
)
def test_reset_as_cqasm_string(cqasm_string: str, expected_result: str) -> None:
    qc = Circuit.from_string(cqasm_string)
    assert str(qc) == expected_result


def test_reset_in_circuit_builder() -> None:
    builder = CircuitBuilder(2)
    builder.reset(0).reset(1)
    qc = builder.to_circuit()
    assert qc.qubit_register_size == 2
    assert qc.qubit_register_name == "q"
    assert qc.ir.statements == [Reset(0), Reset(1)]
