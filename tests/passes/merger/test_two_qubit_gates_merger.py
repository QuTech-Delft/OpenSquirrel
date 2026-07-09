import pytest
from typing import TYPE_CHECKING
from opensquirrel.passes.merger.two_qubit_gates_merger import TwoQubitGatesMerger, group_gates
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.circuit_matrix_calculator import get_circuit_matrix

from tests.ir.ir_equality_test_base import modify_circuit_and_check
from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
# if TYPE_CHECKING:
#     from opensquirrel.circuit import Circuit

@pytest.fixture
def merger() -> TwoQubitGatesMerger:
    return TwoQubitGatesMerger()

@pytest.mark.parametrize(
    "gates, expected_groups",
    [
        ([[0]], [((0,), [0])]),
        ([[0, 1]], [((0, 1), [0])]),
        ([[0, 1], [0, 1], [1, 2], [1, 2]], [((0, 1), [0, 1]), ((1, 2), [2, 3])]),
        ([[0, 1], [], [1, 2], [1, 2]], [((0, 1), [0]), ((1, 2), [2, 3])]),
        ([[0, 1], [0, 1], [], [1, 2], [1, 2]], [((0, 1), [0, 1]), ((1, 2), [3, 4])]),       
        ([[0, 1], [2, 1], [1, 2], [1], [1], [0, 1], [0], [1]], [((0, 1), [0]), ((1, 2), [1, 2, 3, 4]), ((0, 1), [5, 6, 7])]),
    ] 
)
def test_group_gates(gates: list[list[int]], expected_groups: list[tuple[tuple[int, int], list[int]]]) -> None:
    assert group_gates(gates) == expected_groups

@pytest.mark.parametrize(
    "circuit, expected_circuit",
    [
        (CircuitBuilder(1).H(0).to_circuit(), CircuitBuilder(1).H(0).to_circuit()),
        (CircuitBuilder(2).CNOT(0,1).to_circuit(), CircuitBuilder(2).CNOT(0, 1).to_circuit()),
        (CircuitBuilder(2).CNOT(0,1).CNOT(1, 0).CNOT(0, 1).to_circuit(), CircuitBuilder(2).SWAP(0, 1).to_circuit()),
        (CircuitBuilder(2).SWAP(0, 1).SWAP(0, 1).to_circuit(), CircuitBuilder(2).I(0).to_circuit()),
        (CircuitBuilder(2).SWAP(0, 1).CZ(0, 1).S(0).S(1).to_circuit(), CircuitBuilder(2).ISWAP(0, 1).to_circuit()),
        (CircuitBuilder(2).H(1).CNOT(0, 1).H(1).to_circuit(), CircuitBuilder(2).CZ(0, 1).to_circuit()),
        (CircuitBuilder(2).CV(0, 1).CV(0, 1).to_circuit(), CircuitBuilder(2).CNOT(0, 1).to_circuit()),
        (CircuitBuilder(2).H(0).H(1).CNOT(0, 1).H(0).H(1).to_circuit(), CircuitBuilder(2).CNOT(1, 0).to_circuit()),
    ] 
)
def test_two_qubit_gates_merger(circuit, expected_circuit, merger: TwoQubitGatesMerger) -> None:
    modify_circuit_and_check(circuit, merger.merge, expected_circuit)



@pytest.mark.parametrize(
    "circuit, expected_circuit",
    [
        (CircuitBuilder(1).H(0).to_circuit(), CircuitBuilder(1).H(0).to_circuit()),
        (CircuitBuilder(2).CNOT(0, 1).to_circuit(), CircuitBuilder(2).CNOT(0, 1).to_circuit()),
        (CircuitBuilder(2).CNOT(0, 1).CNOT(1, 0).CNOT(0, 1).to_circuit(), CircuitBuilder(2).SWAP(0, 1).to_circuit()),
        (CircuitBuilder(2).SWAP(0, 1).SWAP(0, 1).to_circuit(), CircuitBuilder(2).I(0).to_circuit()),
        (CircuitBuilder(2).SWAP(0, 1).CZ(0, 1).S(0).S(1).to_circuit(), CircuitBuilder(2).ISWAP(0, 1).to_circuit()),
        (CircuitBuilder(2).H(1).CNOT(0, 1).H(1).to_circuit(), CircuitBuilder(2).CZ(0, 1).to_circuit()),
        (CircuitBuilder(2).CV(0, 1).CV(0, 1).to_circuit(), CircuitBuilder(2).CNOT(0, 1).to_circuit()),
        (CircuitBuilder(2).H(0).H(1).CNOT(0, 1).H(0).H(1).to_circuit(), CircuitBuilder(2).CNOT(1, 0).to_circuit()),
    ] 
)
def test_two_qubit_gates_merger_2(circuit, expected_circuit) -> None:
    expected_matrix = get_circuit_matrix(circuit)        
    actual_matrix = get_circuit_matrix(expected_circuit)
    assert are_matrices_equivalent_up_to_global_phase(actual_matrix, expected_matrix)