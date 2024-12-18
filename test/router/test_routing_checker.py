# Tests for routing checker pass

import pytest
from opensquirrel.passes.router.routing_checker import RoutingChecker


@pytest.fixture(name = "router")
def router_fixture() -> RoutingChecker:
    return RoutingChecker()

def test_routing_checker_possible_121_mapping() -> None:
    backend_connectivity_diagram = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1, 4], 3: [1, 4], 4: [2, 3]}
    interactions = [(0, 1), (1, 2), (2, 4), (3, 4)]
    router = RoutingChecker(backend_connectivity_diagram)
    assert router.route(interactions) == "The algorithm can be mapped to the target backend"

def test_routing_checker_impossible_121_mapping() -> None:
    backend_connectivity_diagram = {0: [1], 1: [0, 2], 2: [1, 3], 3: [2, 4], 4: [3]}
    interactions = [(0, 1), (0, 3), (1, 2), (1, 3), (2, 3), (3, 4), (0, 4)]
    router = RoutingChecker(backend_connectivity_diagram)
    assert router.route(interactions) == ValueError