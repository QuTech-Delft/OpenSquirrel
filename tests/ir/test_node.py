import pytest

from opensquirrel.ir import IR, Qubit, Statement
from opensquirrel.ir.node import build_graph
from opensquirrel.ir.statement import Instruction
from opensquirrel import H, CNOT


class TestNodeGraph:
    @pytest.mark.parametrize(
        "statements, expected_edges",
        [
            (
                [H(0), CNOT(0, 1), H(1)],
                {(0, 1), (1, 2)},
            ),
            (
                [H(1), CNOT(0, 1), H(1), H(2), CNOT(1, 2), H(2)],
                {(0, 1), (1, 2), (2, 4), (3, 4), (4, 5)},
            ),
            (
                [H(3), CNOT(2,3), H(1), H(2), CNOT(0, 1), H(2), H(1), H(3), CNOT(1, 2), H(2)],
                {(0,1), (1,3), (1, 7), (6, 8), (2, 4), (4, 6), (3, 5), (5, 8), (8, 9)}
            )
        ],
    )
    def test_build_graph_creates_dependencies(self, statements: list[Statement], expected_edges) -> None:
        ir = IR()
        for statement in statements:
            ir.add_statement(statement)

        graph = build_graph(ir)

        assert set(graph.edges()) == expected_edges


    def test_build_graph_does_not_create_edges_for_unrelated_instructions(self) -> None:
        ir = IR()
        ir.add_statement(H(0))
        ir.add_statement(H(2))
        ir.add_statement(H(1))

        graph = build_graph(ir)

        assert list(graph.edges()) == []

        