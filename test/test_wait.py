import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.ir import Wait


@pytest.mark.parametrize(
    ("cqasm_string", "expected_result"),
    [
        (
            "version 3.0; qubit[2] q; wait(3) q[1]; wait(1) q[0]",
            "version 3.0\n\nqubit[2] q\n\nwait(3) q[1]\nwait(1) q[0]\n",
        ),
        (
            "version 3.0; qubit[4] q; wait(3) q[2:3]; wait(1) q[1, 0]",
            "version 3.0\n\nqubit[4] q\n\nwait(3) q[2]\nwait(3) q[3]\nwait(1) q[1]\nwait(1) q[0]\n",
        ),
    ],
    ids=["wait", "wait sgmq"],
)
def test_wait_as_cqasm_string(cqasm_string: str, expected_result: str) -> None:
    qc = Circuit.from_string(cqasm_string)
    assert str(qc) == expected_result


def test_wait_in_circuit_builder() -> None:
    builder = CircuitBuilder(2)
    builder.wait(0, 3).wait(1, 1)
    qc = builder.to_circuit()
    assert qc.qubit_register_size == 2
    assert qc.qubit_register_name == "q"
    assert qc.ir.statements == [Wait(0, 3), Wait(1, 1)]
