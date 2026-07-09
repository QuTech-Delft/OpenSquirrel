import pytest

from opensquirrel import circuit_matrix_calculator
from opensquirrel.circuit import Circuit
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
from opensquirrel.passes.merger.two_qubit_gates_merger import TwoQubitGatesMerger, group_gates


@pytest.fixture
def merger() -> TwoQubitGatesMerger:
    return TwoQubitGatesMerger()


@pytest.mark.parametrize(
    ("gates", "expected_groups"),
    [
        ([[0]], [((0,), [0])]),
        ([[0, 1]], [((0, 1), [0])]),
        ([[0, 1], [0, 1], [1, 2], [1, 2]], [((0, 1), [0, 1]), ((1, 2), [2, 3])]),
        ([[0, 1], [], [1, 2], [1, 2]], [((0, 1), [0]), ((1, 2), [2, 3])]),
        ([[0, 1], [0, 1], [], [1, 2], [1, 2]], [((0, 1), [0, 1]), ((1, 2), [3, 4])]),
        (
            [[0, 1], [2, 1], [1, 2], [1], [1], [0, 1], [0], [1]],
            [((0, 1), [0]), ((1, 2), [1, 2, 3, 4]), ((0, 1), [5, 6, 7])],
        ),
    ],
)
def test_group_gates(gates: list[list[int]], expected_groups: list[tuple[tuple[int, int], list[int]]]) -> None:
    assert group_gates(gates) == expected_groups


@pytest.mark.parametrize(
    ("circuit", "expected_circuit"),
    [
        (CircuitBuilder(1).H(0).to_circuit(), CircuitBuilder(1).H(0).to_circuit()),
        (CircuitBuilder(2).CNOT(0, 1).to_circuit(), CircuitBuilder(2).CNOT(0, 1).to_circuit()),
        (CircuitBuilder(2).CNOT(0, 1).CNOT(1, 0).CNOT(0, 1).to_circuit(), CircuitBuilder(2).SWAP(0, 1).to_circuit()),
        (CircuitBuilder(2).SWAP(0, 1).SWAP(0, 1).to_circuit(), CircuitBuilder(2).I(0).to_circuit()),
        (CircuitBuilder(2).SWAP(0, 1).CZ(0, 1).S(0).S(1).to_circuit(), CircuitBuilder(2).ISWAP(0, 1).to_circuit()),
        (CircuitBuilder(2).H(1).CNOT(0, 1).H(1).to_circuit(), CircuitBuilder(2).CZ(0, 1).to_circuit()),
        (CircuitBuilder(2).CV(0, 1).CV(0, 1).to_circuit(), CircuitBuilder(2).CNOT(0, 1).to_circuit()),
        (CircuitBuilder(2).H(0).H(1).CNOT(0, 1).H(0).H(1).to_circuit(), CircuitBuilder(2).CNOT(1, 0).to_circuit()),
        (
            CircuitBuilder(2).CV(0, 1).to_circuit(),
            CircuitBuilder(2).T(0).H(1).CNOT(1, 0).Tdag(0).T(1).CNOT(1, 0).H(1).to_circuit(),
        ),
    ],
)
def test_two_qubit_gates_merger_with_two_qubits(
    circuit: Circuit, expected_circuit: Circuit, merger: TwoQubitGatesMerger
) -> None:
    expected_matrix = circuit_matrix_calculator.get_circuit_matrix(expected_circuit)
    pre_merge_matrix = circuit_matrix_calculator.get_circuit_matrix(circuit)

    merger.merge(circuit.ir, circuit.qubit_register_size)

    actual_matrix = circuit_matrix_calculator.get_circuit_matrix(circuit)

    assert are_matrices_equivalent_up_to_global_phase(actual_matrix, pre_merge_matrix)
    assert are_matrices_equivalent_up_to_global_phase(actual_matrix, expected_matrix)

    # Since we are only dealing two qubits, we can check that the number of statements is 1,
    # which means that the two-qubit gates have been merged into a single gate.
    assert len(circuit.ir.statements) == 1


@pytest.mark.parametrize(
    ("circuit", "expected_circuit"),
    [
        (
            CircuitBuilder(3).H(1).CNOT(0, 1).H(1).H(2).CNOT(1, 2).H(2).to_circuit(),
            CircuitBuilder(3).CZ(0, 1).CZ(1, 2).to_circuit(),
        ),
    ],
)
def test_two_qubit_gates_merger_with_multiple_qubits(
    circuit: Circuit, expected_circuit: Circuit, merger: TwoQubitGatesMerger
) -> None:
    expected_matrix = circuit_matrix_calculator.get_circuit_matrix(expected_circuit)
    pre_merge_matrix = circuit_matrix_calculator.get_circuit_matrix(circuit)

    merger.merge(circuit.ir, circuit.qubit_register_size)

    actual_matrix = circuit_matrix_calculator.get_circuit_matrix(circuit)

    assert are_matrices_equivalent_up_to_global_phase(actual_matrix, pre_merge_matrix)
    assert are_matrices_equivalent_up_to_global_phase(actual_matrix, expected_matrix)
