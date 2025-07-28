import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.exceptions import NoRoutingPathError
from opensquirrel.passes.router import AStarRouter, ShortestPathRouter
from opensquirrel.passes.router.heuristics import DistanceMetric


class TestAStarRouter:
    def test_example_1(self) -> None:
        connectivity = {"0": [1], "1": [0, 2], "2": [1, 3], "3": [2, 4], "4": [3]}

        builder = CircuitBuilder(5)
        builder.CNOT(0, 1)
        builder.CNOT(1, 2)
        builder.CNOT(2, 3)
        builder.CNOT(3, 4)
        builder.CNOT(0, 4)
        circuit = builder.to_circuit()

        a_star_router = AStarRouter(connectivity=connectivity, distance_metric=DistanceMetric.MANHATTAN)
        circuit.route(router=a_star_router)

        assert (
            str(circuit)
            == """version 3.0

qubit[5] q

CNOT q[0], q[1]
CNOT q[1], q[2]
CNOT q[2], q[3]
CNOT q[3], q[4]
SWAP q[0], q[1]
SWAP q[1], q[2]
SWAP q[2], q[3]
CNOT q[3], q[4]
"""
        )

    def test_example_2(self) -> None:
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
        circuit = builder.to_circuit()

        a_star_router = AStarRouter(connectivity=connectivity, distance_metric=DistanceMetric.CHEBYSHEV)
        circuit.route(router=a_star_router)

        assert (
            str(circuit)
            == """version 3.0

qubit[10] q

SWAP q[0], q[2]
SWAP q[2], q[4]
CNOT q[4], q[9]
SWAP q[1], q[6]
CNOT q[6], q[8]
SWAP q[0], q[2]
CNOT q[2], q[7]
CNOT q[3], q[6]
CNOT q[0], q[5]
CNOT q[4], q[2]
SWAP q[6], q[1]
CNOT q[1], q[3]
SWAP q[0], q[1]
CNOT q[1], q[6]
CNOT q[5], q[7]
CNOT q[8], q[9]
SWAP q[4], q[2]
SWAP q[2], q[0]
CNOT q[0], q[5]
SWAP q[2], q[4]
CNOT q[4], q[6]
SWAP q[2], q[4]
SWAP q[4], q[9]
CNOT q[9], q[8]
SWAP q[3], q[8]
SWAP q[8], q[9]
CNOT q[9], q[9]
"""
        )

    def test_example_3(self) -> None:
        connectivity = {"0": [1], "1": [0], "2": [3], "3": [2]}

        builder = CircuitBuilder(4)
        builder.CNOT(0, 2)
        builder.CNOT(3, 1)
        circuit = builder.to_circuit()

        a_star_router = AStarRouter(connectivity=connectivity, distance_metric=DistanceMetric.EUCLIDEAN)
        with pytest.raises(NoRoutingPathError, match=r"No routing path available between qubit 0 and qubit 2"):
            circuit.route(router=a_star_router)


class TestShortestPathRouter:
    def test_example_1(self) -> None:
        connectivity = {"0": [1], "1": [0, 2], "2": [1, 3], "3": [2, 4], "4": [3]}

        builder = CircuitBuilder(5)
        builder.CNOT(0, 1)
        builder.CNOT(1, 2)
        builder.CNOT(2, 3)
        builder.CNOT(3, 4)
        builder.CNOT(0, 4)
        circuit = builder.to_circuit()

        shortest_path_router = ShortestPathRouter(connectivity=connectivity)
        circuit.route(router=shortest_path_router)

        assert (
            str(circuit)
            == """version 3.0

qubit[5] q

CNOT q[0], q[1]
CNOT q[1], q[2]
CNOT q[2], q[3]
CNOT q[3], q[4]
SWAP q[0], q[1]
SWAP q[1], q[2]
SWAP q[2], q[3]
CNOT q[3], q[4]
"""
        )

    def test_example_2(self) -> None:
        connectivity = {"0": [1, 2], "1": [0, 3], "2": [0, 4], "3": [1, 5], "4": [2, 5], "5": [3, 4, 6], "6": [5]}

        builder = CircuitBuilder(7)
        builder.CNOT(0, 6)
        builder.CNOT(1, 5)
        builder.CNOT(2, 4)
        builder.CNOT(3, 6)
        builder.CNOT(0, 2)
        builder.CNOT(1, 3)
        builder.CNOT(4, 5)
        builder.CNOT(5, 6)
        circuit = builder.to_circuit()

        shortest_path_router = ShortestPathRouter(connectivity=connectivity)
        circuit.route(router=shortest_path_router)

        assert (
            str(circuit)
            == """version 3.0

qubit[7] q

SWAP q[0], q[1]
SWAP q[1], q[3]
SWAP q[3], q[5]
CNOT q[5], q[6]
SWAP q[0], q[1]
CNOT q[1], q[5]
CNOT q[2], q[4]
SWAP q[0], q[1]
SWAP q[1], q[3]
SWAP q[3], q[5]
CNOT q[5], q[6]
SWAP q[3], q[1]
SWAP q[1], q[0]
CNOT q[0], q[2]
SWAP q[1], q[3]
CNOT q[3], q[3]
SWAP q[4], q[2]
SWAP q[2], q[0]
CNOT q[0], q[5]
SWAP q[1], q[3]
SWAP q[3], q[5]
CNOT q[5], q[6]
"""
        )

    def test_example_3(self) -> None:
        connectivity = {"0": [1], "1": [0], "2": [3], "3": [2]}

        builder = CircuitBuilder(4)
        builder.CNOT(0, 2)
        builder.CNOT(3, 1)
        circuit = builder.to_circuit()

        shortest_path_router = ShortestPathRouter(connectivity=connectivity)

        with pytest.raises(NoRoutingPathError, match=r"No routing path available between qubit 0 and qubit 2"):
            circuit.route(router=shortest_path_router)
