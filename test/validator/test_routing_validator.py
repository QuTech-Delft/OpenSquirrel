# Tests for routing validator pass

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import Circuit
from opensquirrel.passes.validator import RoutingValidator


@pytest.fixture(name="validator")
def router_fixture() -> RoutingValidator:
    connectivity = {"0": [1, 2], "1": [0, 2, 3], "2": [0, 1, 4], "3": [1, 4], "4": [2, 3]}
    return RoutingValidator(connectivity)


@pytest.fixture
def circuit1() -> Circuit:
    builder = CircuitBuilder(5)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.H(2)
    builder.CNOT(1, 2)
    builder.CNOT(2, 4)
    builder.CNOT(3, 4)
    return builder.to_circuit()


@pytest.fixture
def circuit2() -> Circuit:
    builder = CircuitBuilder(5)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.CNOT(0, 3)
    builder.H(2)
    builder.CNOT(1, 2)
    builder.CNOT(1, 3)
    builder.CNOT(2, 3)
    builder.CNOT(3, 4)
    builder.CNOT(0, 4)
    return builder.to_circuit()


def test_routing_checker_possible_1to1_mapping(validator: RoutingValidator, circuit1: Circuit) -> None:
    try:
        validator.validate(circuit1.ir)
    except ValueError:
        pytest.fail("route() raised ValueError unexpectedly")


def test_routing_checker_impossible_1to1_mapping(validator: RoutingValidator, circuit2: Circuit) -> None:
    with pytest.raises(
        ValueError, match=r"the following qubit interactions in the circuit prevent a 1-to-1 mapping:.*"
    ):
        validator.validate(circuit2.ir)
