# Tests for routing checker pass

import pytest
from opensquirrel.passes.router.routing_checker import RoutingChecker

@pytest.fixture(name="router")
def router_fixture() -> RoutingChecker:
    backend_connectivity_diagram = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1, 4], 3: [1, 4], 4: [2, 3]}
    return RoutingChecker(backend_connectivity_diagram)

def test_routing_checker_possible_121_mapping(router: RoutingChecker) -> None:
    interactions = [(0, 1), (1, 2), (2, 4), (3, 4)]
    try:
        router.route(interactions)
    except ValueError:
        pytest.fail("route() raised ValueError unexpectedly!")

def test_routing_checker_impossible_121_mapping(router: RoutingChecker) -> None:
    interactions = [(0, 1), (0, 3), (1, 2), (1, 3), (2, 3), (3, 4), (0, 4)]
    with pytest.raises(ValueError):
        router.route(interactions)