import pytest

from opensquirrel import CNOT, H, circuit_matrix_calculator
from opensquirrel.circuit import Circuit
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
from opensquirrel.ir import IR, Statement
from opensquirrel.passes.merger.two_qubit_gates_merger import TwoQubitGatesMerger, build_graph, group_gates


class TestNodeGraph:
    @pytest.mark.parametrize(
        ("statements", "expected_edges"),
        [
            (
                [H(0), H(1), H(2)],
                set(),
            ),
            (
                [H(0), CNOT(0, 1), H(1)],
                {(0, 1), (1, 2)},
            ),
            (
                [H(1), CNOT(0, 1), H(1), H(2), CNOT(1, 2), H(2)],
                {(0, 1), (1, 2), (2, 4), (3, 4), (4, 5)},
            ),
            (
                [H(3), CNOT(2, 3), H(1), H(2), CNOT(0, 1), H(2), H(1), H(3), CNOT(1, 2), H(2)],
                {(0, 1), (1, 3), (1, 7), (6, 8), (2, 4), (4, 6), (3, 5), (5, 8), (8, 9)},
            ),
        ],
    )
    def test_build_graph_creates_dependencies(
        self, statements: list[Statement], expected_edges: set[tuple[int, int]]
    ) -> None:
        ir = IR()
        for statement in statements:
            ir.add_statement(statement)

        graph = build_graph(ir)

        assert set(graph.edges()) == expected_edges

    @pytest.mark.parametrize(
        ("statements", "expected"),
        [
            ([H(0)], [({0}, {0})]),
            ([CNOT(0, 1)], [({0}, {0, 1})]),
            ([H(0), CNOT(0, 1), H(1)], [({0, 1, 2}, {0, 1})]),
            ([H(1), CNOT(0, 1), H(1), H(2), CNOT(1, 2), H(2)], [({0, 1, 2}, {0, 1}), ({3, 4, 5}, {1, 2})]),
            (
                [H(3), CNOT(2, 3), H(1), H(2), CNOT(0, 1), H(2), H(1), H(3), CNOT(1, 2), H(2)],
                [({0, 1, 3, 5, 7}, {2, 3}), ({2, 4, 6}, {0, 1}), ({8, 9}, {1, 2})],
            ),
            (
                [H(2), H(0), CNOT(0, 1), CNOT(1, 2), CNOT(2, 3), H(1), H(3), H(0), H(2)],
                [({1, 2, 7}, {0, 1}), ({0, 3, 5}, {1, 2}), ({4, 6, 8}, {2, 3})],
            ),
        ],
    )
    def test_group_gates(self, statements: list[Statement], expected: list[tuple[set[int], set[int]]]) -> None:
        ir = IR()
        for statement in statements:
            ir.add_statement(statement)

        graph = build_graph(ir)

        assert group_gates(graph) == expected


@pytest.fixture
def merger() -> TwoQubitGatesMerger:
    return TwoQubitGatesMerger()


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
            CircuitBuilder(2).T(0).H(1).CNOT(1, 0).Tdag(0).T(1).CNOT(1, 0).H(1).to_circuit(),
            CircuitBuilder(2).CV(0, 1).to_circuit(),
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
