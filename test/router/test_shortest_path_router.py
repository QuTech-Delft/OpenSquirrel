# Tests for the ShortestPathRouter class
import pytest
from pytest_lazy_fixtures import lf

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.ir import SWAP
from opensquirrel.passes.router import ShortestPathRouter


@pytest.fixture(name="router1")
def router_fixture1() -> ShortestPathRouter:
    connectivity = {"0": [1], "1": [0, 2], "2": [1, 3], "3": [2, 4], "4": [3]}
    return ShortestPathRouter(connectivity)


@pytest.fixture(name="router2")
def router_fixture2() -> ShortestPathRouter:
    connectivity = {"0": [1, 2], "1": [0, 3], "2": [0, 4], "3": [1, 5], "4": [2, 5], "5": [3, 4, 6], "6": [5]}
    return ShortestPathRouter(connectivity)


@pytest.fixture(name="router3")
def router_fixture3() -> ShortestPathRouter:
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
    return ShortestPathRouter(connectivity)


@pytest.fixture(name="circuit1")
def circuit_fixture1() -> Circuit:
    builder = CircuitBuilder(5)
    builder.CNOT(0, 1)
    builder.CNOT(1, 2)
    builder.CNOT(2, 3)
    builder.CNOT(3, 4)
    builder.CNOT(0, 4)
    return builder.to_circuit()


@pytest.fixture(name="circuit2")
def circuit_fixture2() -> Circuit:
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


@pytest.fixture(name="circuit3")
def circuit_fixture3() -> Circuit:
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


@pytest.mark.parametrize(
    "router, circuit, expected_swap_count",  # noqa: PT006
    [(lf("router1"), lf("circuit1"), 4), (lf("router2"), lf("circuit2"), 8), (lf("router3"), lf("circuit3"), 15)],
)
def test_router(router: ShortestPathRouter, circuit: Circuit, expected_swap_count: int) -> None:
    new_ir = router.route(circuit.ir)
    swap_count = sum(1 for statement in new_ir.statements if isinstance(statement, SWAP))
    assert swap_count == expected_swap_count
