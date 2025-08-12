# Tests for the AStarRouter class
import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.ir.default_gates import SWAP
from opensquirrel.passes.router import AStarRouter
from opensquirrel.passes.router.heuristics import DistanceMetric


@pytest.fixture
def router1() -> AStarRouter:
    connectivity = {"0": [1], "1": [0, 2], "2": [1, 3], "3": [2, 4], "4": [3]}
    return AStarRouter(connectivity, distance_metric=DistanceMetric.MANHATTAN)


@pytest.fixture
def router2() -> AStarRouter:
    connectivity = {"0": [1, 2], "1": [0, 3], "2": [0, 4], "3": [1, 5], "4": [2, 5], "5": [3, 4, 6], "6": [5]}
    return AStarRouter(connectivity, distance_metric=DistanceMetric.EUCLIDEAN)


@pytest.fixture
def router3() -> AStarRouter:
    connectivity = {
        "0": [1, 2, 5],
        "1": [0, 3, 6],
        "2": [0, 4, 7],
        "3": [1, 5, 8],
        "4": [2, 6, 9],
        "5": [0, 3, 7],
        "6": [1, 4, 8],
        "7": [2, 5, 9],
        "8": [3, 6, 9],
        "9": [4, 7, 8],
    }
    return AStarRouter(connectivity, distance_metric=DistanceMetric.CHEBYSHEV)


@pytest.fixture
def router4() -> AStarRouter:
    connectivity = {
        "0": [1],
        "1": [0, 2],
        "2": [1, 3],
        "3": [2],
    }
    return AStarRouter(connectivity, distance_metric=DistanceMetric.MANHATTAN)


@pytest.fixture
def circuit1() -> Circuit:
    builder = CircuitBuilder(5)
    builder.CNOT(0, 1)
    builder.CNOT(1, 2)
    builder.CNOT(2, 3)
    builder.CNOT(3, 4)
    builder.CNOT(0, 4)
    return builder.to_circuit()


@pytest.fixture
def circuit2() -> Circuit:
    builder = CircuitBuilder(7)
    builder.CNOT(0, 6)
    builder.CNOT(1, 5)
    builder.CNOT(2, 4)
    builder.CNOT(3, 6)
    builder.CNOT(0, 2)
    builder.CNOT(1, 3)
    builder.CNOT(4, 5)
    builder.CNOT(5, 6)
    return builder.to_circuit()


@pytest.fixture
def circuit3() -> Circuit:
    builder = CircuitBuilder(10)
    builder.CNOT(0, 9)
    builder.CNOT(1, 8)
    builder.CNOT(2, 7)
    builder.CNOT(3, 6)
    builder.CNOT(4, 5)
    builder.CNOT(0, 2)
    builder.CNOT(1, 3)
    builder.CNOT(4, 6)
    builder.CNOT(5, 7)
    builder.CNOT(8, 9)
    builder.CNOT(0, 5)
    builder.CNOT(1, 6)
    builder.CNOT(2, 8)
    builder.CNOT(3, 9)
    return builder.to_circuit()


@pytest.fixture
def circuit4() -> Circuit:
    builder = CircuitBuilder(4)
    builder.CNOT(0, 3)
    builder.CNOT(1, 2)
    return builder.to_circuit()


@pytest.mark.parametrize(
    "router, circuit, expected_swap_count",  # noqa: PT006
    [("router1", "circuit1", 3), ("router2", "circuit2", 15), ("router3", "circuit3", 13)],
)
def test_router(
    router: AStarRouter, circuit: Circuit, expected_swap_count: int, request: pytest.FixtureRequest
) -> None:
    circuit = request.getfixturevalue(circuit)  # type: ignore[arg-type]
    router = request.getfixturevalue(router)  # type: ignore[arg-type]
    circuit.route(router=router)
    swap_count = sum(1 for statement in circuit.ir.statements if isinstance(statement, SWAP))
    assert swap_count == expected_swap_count


def test_route_on_circuit(router4: AStarRouter, circuit4: Circuit) -> None:
    circuit4.route(router=router4)
    swap_count = sum(1 for statement in circuit4.ir.statements if isinstance(statement, SWAP))
    assert swap_count == 2


def test_route_indices_propagation(router4: AStarRouter, circuit4: Circuit) -> None:
    circuit4.route(router=router4)

    builder = CircuitBuilder(4)
    builder.SWAP(0, 1)
    builder.SWAP(1, 2)
    builder.CNOT(2, 3)
    builder.CNOT(0, 1)
    expected_circuit = builder.to_circuit()

    actual_statements = circuit4.ir.statements
    expected_statements = expected_circuit.ir.statements

    assert len(actual_statements) == len(expected_statements)

    for actual, expected in zip(actual_statements, expected_statements):
        assert type(actual) is type(expected)
        actual_indices = [q.index for q in actual.get_qubit_operands()]  # type: ignore[attr-defined]
        expected_indices = [q.index for q in expected.get_qubit_operands()]  # type: ignore[attr-defined]
        assert actual_indices == expected_indices
