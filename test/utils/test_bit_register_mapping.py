import math
from collections.abc import Iterable

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.default_instructions import measure
from opensquirrel.ir import Measure
from opensquirrel.utils.bit_register_mapping import BitStringMapping


@pytest.fixture(name="bit_string_mapping")
def bit_string_mapping_fixture() -> BitStringMapping:
    return BitStringMapping()


@pytest.mark.parametrize(
    ("measurements", "expected_mapping", "expected_bit_allocation"),
    [
        ([measure(0, 0)], {0: [0]}, {0: 0}),
        ([measure(0, 0), measure(1, 0)], {0: [0], 1: [0]}, {0: 1}),
        ([measure(0, 1), measure(0, 0)], {0: [1, 0]}, {0: 0, 1: 0}),
    ],
)
def test_add_measure(
    bit_string_mapping: BitStringMapping,
    measurements: Iterable[Measure],
    expected_mapping: dict[int, list[int]],
    expected_bit_allocation: dict[int, int],
) -> None:
    for measurement in measurements:
        bit_string_mapping.add_measure(measurement)
    assert bit_string_mapping._mapping == expected_mapping
    assert bit_string_mapping._bit_allocation == expected_bit_allocation


def test_get_last_added_acq_channel_and_index(bit_string_mapping: BitStringMapping) -> None:
    bit_string_mapping.add_measure(measure(0, 0))
    assert bit_string_mapping.get_last_added_acq_channel_and_index() == (0, 0)
    bit_string_mapping.add_measure(measure(0, 0))
    assert bit_string_mapping.get_last_added_acq_channel_and_index() == (0, 1)
    bit_string_mapping.add_measure(measure(1, 0))
    assert bit_string_mapping.get_last_added_acq_channel_and_index() == (1, 0)
    bit_string_mapping.add_measure(measure(2, 1))
    assert bit_string_mapping.get_last_added_acq_channel_and_index() == (2, 0)


def test_get_last_added_acq_channel_and_index_error(bit_string_mapping: BitStringMapping) -> None:
    with pytest.raises(ValueError, match="BitStringMapping is empty, so there is no acq to get"):
        bit_string_mapping.get_last_added_acq_channel_and_index()


def test_to_export_format(bit_string_mapping: BitStringMapping) -> None:
    builder = CircuitBuilder(3, 4)
    builder.Rx(0, math.pi)
    builder.measure(0, 0)
    builder.Rx(1, math.pi)
    builder.measure(1, 1)
    builder.Rx(2, math.pi)
    builder.measure(2, 0)
    builder.Rx(0, math.pi)
    builder.measure(0, 2)

    circuit = builder.to_circuit()

    for instruction in circuit.ir.statements:
        if isinstance(instruction, Measure):
            bit_string_mapping.add_measure(instruction)

    expected_output = {"0": {"1": 2}, "1": {"0": 1}, "2": {"0": 0}}
    assert bit_string_mapping.to_export_format() == expected_output
