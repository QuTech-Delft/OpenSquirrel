import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.ir import Init


@pytest.mark.parametrize(
    ("cqasm_string", "expected_result"),
    [
        (
            "version 3.0; qubit[2] q; init q[1]; init q[0]",
            "version 3.0\n\nqubit[2] q\n\ninit q[1]\ninit q[0]\n",
        ),
        (
            "version 3.0; qubit[4] q; init q[2:3]; init q[1, 0]",
            "version 3.0\n\nqubit[4] q\n\ninit q[2]\ninit q[3]\ninit q[1]\ninit q[0]\n",
        ),
    ],
    ids=["init", "init sgmq"],
)
def test_init_as_cqasm_string(cqasm_string: str, expected_result: str) -> None:
    circuit = Circuit.from_string(cqasm_string)
    assert str(circuit) == expected_result


def test_init_in_circuit_builder() -> None:
    builder = CircuitBuilder(2)
    builder.init(0).init(1)
    circuit = builder.to_circuit()
    assert circuit.qubit_register_size == 2
    assert circuit.qubit_register_names()[0] == "q"
    assert circuit.ir.statements == [Init(0), Init(1)]
