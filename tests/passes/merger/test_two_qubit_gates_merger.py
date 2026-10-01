import numpy as np
import pytest

from opensquirrel import CNOT, H, circuit_matrix_calculator
from opensquirrel.circuit import Circuit
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
from opensquirrel.ir import IR, AsmDeclaration, Gate, Statement, Wait
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
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
            (
                [
                    H(0),
                    H(1),
                    AsmDeclaration("backend", "code"),
                    H(0),
                    CNOT(0, 1),
                    H(0),
                    AsmDeclaration("backend", "code"),
                    H(1),
                    CNOT(1, 2),
                    H(1),
                ],
                {
                    (0, 2),
                    (1, 2),
                    (2, 3),
                    (2, 4),
                    (2, 6),
                    (3, 4),
                    (4, 5),
                    (4, 6),
                    (5, 6),
                    (6, 7),
                    (6, 8),
                    (7, 8),
                    (8, 9),
                },
            ),
            (
                [H(0), H(1), CNOT(0, 1), H(0), H(1)],
                {(0, 2), (1, 2), (2, 3), (2, 4)},
            ),
            ([CNOT(0, 1), CNOT(0, 2), CNOT(1, 2), CNOT(1, 0)], {(0, 1), (0, 2), (1, 2), (2, 3), (1, 3)}),
            (
                [
                    H(0),
                    CNOT(1, 0),
                    H(2),
                    H(0),
                    H(3),
                    CNOT(1, 2),
                    CNOT(0, 3),
                    H(3),
                    H(0),
                    CNOT(1, 0),
                    H(2),
                    H(0),
                ],
                {(0, 1), (1, 3), (1, 5), (2, 5), (4, 6), (3, 6), (5, 10), (5, 9), (8, 9), (9, 11), (6, 7), (6, 8)},
            ),
            (
                [H(0), H(1), Wait(0, 1), CNOT(0, 1), H(1), Wait(1, 1), H(1)],
                {(0, 2), (1, 3), (2, 3), (3, 4), (4, 5), (5, 6)},
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
            ([H(0), H(1), CNOT(0, 1), H(0), H(1)], [({0, 1, 2, 3, 4}, {0, 1})]),
            ([CNOT(0, 1), CNOT(1, 2), CNOT(0, 1)], [({0}, {0, 1}), ({1}, {1, 2}), ({2}, {0, 1})]),
            (
                [CNOT(0, 1), CNOT(0, 2), CNOT(1, 2), CNOT(1, 0)],
                [({0}, {0, 1}), ({1}, {0, 2}), ({2}, {1, 2}), ({3}, {1, 0})],
            ),
            (
                [
                    H(0),
                    CNOT(1, 0),
                    H(2),
                    H(0),
                    H(3),
                    CNOT(1, 2),
                    CNOT(0, 3),
                    H(3),
                    H(0),
                    CNOT(1, 0),
                    H(2),
                    H(0),
                ],
                [({0, 1, 3}, {0, 1}), ({2, 5, 10}, {1, 2}), ({4, 6, 7, 8}, {0, 3}), ({9, 11}, {0, 1})],
            ),
            (
                [
                    H(0),
                    H(1),
                    AsmDeclaration("backend", "code"),
                    H(0),
                    CNOT(0, 1),
                    H(0),
                    AsmDeclaration("backend", "code"),
                    H(1),
                    CNOT(1, 2),
                    H(1),
                ],
                [({0}, {0}), ({1}, {1}), ({2}, set()), ({3, 4, 5}, {0, 1}), ({6}, set()), ({7, 8, 9}, {1, 2})],
            ),
            (
                [H(0), H(1), Wait(0, 1), CNOT(0, 1), H(1), Wait(1, 1), H(1)],
                [({0}, {0}), ({2}, set()), ({1, 3, 4}, {0, 1}), ({5}, set()), ({6}, {1})],
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
        (CircuitBuilder(5).H(2).CNOT(4, 2).H(2).to_circuit(), CircuitBuilder(5).CZ(4, 2).to_circuit()),
        (CircuitBuilder(5).H(4).H(4).CNOT(4, 2).to_circuit(), CircuitBuilder(5).CNOT(4, 2).to_circuit()),
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
        (
            CircuitBuilder(4)
            .H(0)
            .CNOT(1, 0)
            .H(2)
            .H(0)
            .H(3)
            .CNOT(1, 2)
            .CNOT(0, 3)
            .H(3)
            .H(0)
            .CNOT(1, 0)
            .H(2)
            .H(0)
            .to_circuit(),
            CircuitBuilder(4).CZ(1, 0).CZ(1, 2).CZ(0, 3).CZ(0, 1).to_circuit(),
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


@pytest.mark.parametrize(
    ("circuit", "expected_circuit"),
    [
        (
            CircuitBuilder(3)
            .H(0)
            .H(1)
            .asm("backend", "code")
            .H(1)
            .CNOT(0, 1)
            .H(1)
            .asm("backend", "code")
            .H(2)
            .CNOT(1, 2)
            .H(2)
            .to_circuit(),
            CircuitBuilder(3).H(0).H(1).asm("backend", "code").CZ(0, 1).asm("backend", "code").CZ(1, 2).to_circuit(),
        ),
        (
            CircuitBuilder(1).H(0).barrier(0).H(0).to_circuit(),
            CircuitBuilder(1).H(0).barrier(0).H(0).to_circuit(),
        ),
        (
            CircuitBuilder(2).H(0).H(1).wait(0, 1).CNOT(0, 1).H(1).wait(1, 1).H(1).to_circuit(),
            CircuitBuilder(2).H(0).wait(0, 1).CZ(0, 1).wait(1, 1).H(1).to_circuit(),
        ),
    ],
)
def test_two_qubit_gates_merger_with_non_instructions(
    circuit: Circuit, expected_circuit: Circuit, merger: TwoQubitGatesMerger
) -> None:
    merger.merge(circuit.ir, circuit.qubit_register_size)

    for statement1, statement2 in zip(circuit.ir.statements, expected_circuit.ir.statements, strict=True):
        if not isinstance(statement1, Gate) or not isinstance(statement2, Gate):
            assert type(statement1) is type(statement2)
        elif isinstance(statement1, (TwoQubitGate, SingleQubitGate)) and isinstance(
            statement2, (TwoQubitGate, SingleQubitGate)
        ):
            assert np.allclose(statement1.matrix, statement2.matrix)
        else:
            msg = (
                f"Unexpected statement types: {type(statement1)} and {type(statement2)}. "
                "Both should be either TwoQubitGate or SingleQubitGate."
            )
            raise TypeError(msg)
