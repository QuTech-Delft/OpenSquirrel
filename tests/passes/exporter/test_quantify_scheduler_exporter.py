from __future__ import annotations

import importlib
import sys
import unittest.mock
from collections.abc import Generator
from math import degrees, isclose, pi
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.common import ATOL
from opensquirrel.exceptions import ExporterError
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.passes.exporter import ExportFormat
from opensquirrel.passes.exporter.quantify_scheduler_exporter import CYCLE_TIME

if TYPE_CHECKING:
    from opensquirrel.ir import Gate

    try:
        from quantify_scheduler import Schedule
    except ModuleNotFoundError:
        pass


class FloatEq(float):
    def __eq__(self, other: Any) -> bool:
        return isclose(self, other, abs_tol=ATOL)


def _check_ref_schedulables(exported_schedule: Schedule, expected_ref_schedulable_indices: list[int | None]) -> None:
    ref_schedulables = [
        schedulable_data["timing_constraints"][0]["ref_schedulable"]
        for schedulable_data in list(exported_schedule.schedulables.values())
    ]
    schedulable_index_map = {
        None: None,
        **{schedulable: index for index, schedulable in enumerate(list(exported_schedule.schedulables.keys()))},
    }
    for ref_schedulable, expected_ref_schedulable_index in zip(
        ref_schedulables, expected_ref_schedulable_indices, strict=False
    ):
        assert schedulable_index_map[ref_schedulable] == expected_ref_schedulable_index


def _check_waiting_cycles(exported_schedule: Schedule, expected_waiting_cycles: list[int]) -> None:
    for schedulable_data, expected_waiting_cycle in zip(
        exported_schedule.schedulables.values(), expected_waiting_cycles, strict=False
    ):
        waiting_time = schedulable_data.data["timing_constraints"][0]["rel_time"]
        assert waiting_time == -1.0 * expected_waiting_cycle * CYCLE_TIME


@pytest.fixture
def qs_is_installed() -> bool:
    return importlib.util.find_spec("quantify_scheduler") is not None


def test_empty_circuit_export(qs_is_installed: bool) -> None:
    if qs_is_installed:
        circuit = CircuitBuilder(1).to_circuit()
        exported_schedule, _ = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        assert len(exported_schedule.schedulables) == 0


@pytest.mark.parametrize(
    ("cqasm_string", "expected_ref_schedulable_indices"),
    [
        (
            """version 3; qubit[5] q; bit[5] b; reset q; barrier q; X q[0]; X q[0:1]; X q[0:2]; X q[0:3]; X q[0:4];
        barrier q; b = measure q""",
            [5, 5, 5, 5, 5, 6, 8, 9, 11, 12, 13, 15, 16, 17, 18, 24, 24, 24, 24, 24, None, None, None, None, None],
        ),
        (
            """version 3; qubit[5] q; bit[2] b; init q; barrier q; X q[3]; barrier q[3,4]; X q[4]; barrier q[3,4];
        X q[4]; b[0,1] = measure q[3,4]""",
            [5, 5, 5, 5, 5, 6, 7, 9, None, None],
        ),
        (
            """version 3; qubit[5] q; bit[5] b; init q; barrier q; mY90 q[2]; CNOT q[2], q[0]; CNOT q[2], q[1];
        CNOT q[2], q[3]; CNOT q[2], q[4]; barrier q; b[0:4] = measure q[0:4]""",
            [5, 5, 5, 5, 5, 6, 7, 8, 9, 14, None, None, None, None, None],
        ),
        (
            """version 3; qubit[5] q; bit[2] b; init q[3]; init q[2]; barrier q[3]; barrier q[2]; Ry(2.5707963) q[3];
        Ry(-1.5707963) q[3]; Ry(-1.5707963) q[2]; CZ q[3], q[2]; Ry(1.5707963) q[2]; barrier q[3]; barrier q[2];
        b[0] = measure q[3]; b[1] = measure q[2]""",
            [2, 2, 3, 5, 5, 6, 8, None, None],
        ),
        (
            """version 3; qubit[6] q; bit[6] b; init q; barrier q; X q[1]; CNOT q[4], q[5]; CNOT q[1], q[0];
        CNOT q[3], q[4]; CNOT q[2], q[1]; CNOT q[3], q[2]; barrier q; X q[4]; b = measure q""",
            [6, 6, 6, 6, 6, 6, 8, 9, 10, 11, 11, 12, 17, None, None, None, None, None, None],
        ),
        (
            """version 3; qubit[5] q; bit[5] b; init q; barrier q[0:2]; X q[0]; X q[1]; barrier q; X q[2]; X q[3];
            X q[4]; barrier q[1,3]; CNOT q[1], q[3]; barrier q; b = measure q""",
            [6, 6, 6, 8, 8, 8, 8, 15, 10, 15, 15, None, None, None, None, None],
        ),
    ],
    ids=["alap_1", "alap_2", "alap_3", "alap_4", "alap_5", "alap_6"],
)
def test_alap(qs_is_installed: bool, cqasm_string: str, expected_ref_schedulable_indices: list[int | None]) -> None:
    if qs_is_installed:
        circuit = Circuit.from_string(cqasm_string)
        exported_schedule, _ = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        _check_ref_schedulables(exported_schedule, expected_ref_schedulable_indices)


@pytest.mark.parametrize(
    ("cqasm_string", "expected_ref_schedulable_indices", "expected_waiting_cycles"),
    [
        (
            """version 3; qubit[2] q; X q[0]; barrier q; X q[1]; wait(2) q[1]; X q[0]; X q[0]; barrier q; X q[1]""",
            [1, 4, 3, 4, None],
            [0, 2, 0, 0, 0],
        ),
        (
            """version 3; qubit[2] q; CNOT q[0], q[1]; X q[0]; wait(3) q[0]; X q[1]; X q[1]""",
            [1, None, 3, None],
            [0, 3, 0, 0],
        ),
        (
            """version 3; qubit[2] q; CZ q[0], q[1] ;wait(2) q[0]; wait(1) q[1]; X q""",
            [1, None, None],
            [2, 0, 0],
        ),
        (
            """version 3; qubit[2] q; X q; barrier q; wait(1) q[0]; wait(2) q[1]; barrier q; X q[0];
            barrier q; wait(2) q[0]; wait(1) q[1]; barrier q; X q""",
            [2, 2, 4, None, None],
            [2, 2, 2, 0, 0],
        ),
        (
            """version 3; qubit[2] q; X q[0]; barrier q; X q[1]; wait(2) q[1]; X q[0]; wait(4) q[0]; X q[1]""",
            [2, 3, None, None],
            [0, 2, 4, 0],
        ),
        (
            """version 3; qubit[3] q; X q; wait(4) q[0]; barrier q[0]; X q[0]; wait(2) q[1]; barrier q[1];
            CNOT q[1], q[2]; barrier q; X q""",
            [3, 4, 4, 7, 7, None, None, None],
            [4, 2, 0, 0, 0, 0, 0, 0, 0],
        ),
        (
            """version 3; qubit[2] q; X q; barrier q; wait(1) q[0]; wait(2) q[1]; barrier q; X q[0];
            wait(2) q[0]; wait(1) q[1]; barrier q; X q""",
            [2, 2, 4, None, None],
            [2, 2, 2, 0, 0],
        ),
        (
            """version 3; qubit[2] q; X q; barrier q; wait(1) q[0]; wait(2) q[1]; barrier q; X q[0];
            wait(2) q[0]; wait(4) q[1]; barrier q; X q""",
            [4, 4, 4, None, None, None],
            [6, 6, 2, 0, 0],
        ),
        (
            """version 3; qubit[2] q; X q[0]; wait(2) q[0]; wait(3) q[0]; X q[1]; wait(1) q[1]; X q""",
            [2, 3, None, None],
            [5, 1, 0, 0],
        ),
        (
            """version 3; qubit q; X q; wait(-1) q; X q""",
            [1, None],
            [-1, 0],
        ),
        (
            """version 3; qubit q; wait(1) q; X q""",
            [None],
            [0],
        ),
        (
            """version 3; qubit q; X q; wait(1) q""",
            [None],
            [1],
        ),
    ],
    ids=[
        "wait_simple",
        "wait_two_qubit_gate_1",
        "wait_two_qubit_gate_2",
        "wait_two_qubit_gate_3",
        "wait_with_barriers_1",
        "wait_with_barriers_2",
        "wait_with_barriers_3",
        "wait_with_barriers_4",
        "wait_multiple",
        "wait_negative",
        "wait_begin",
        "wait_end",
    ],
)
def test_wait(
    qs_is_installed: bool,
    cqasm_string: str,
    expected_ref_schedulable_indices: list[int | None],
    expected_waiting_cycles: list[int],
) -> None:
    if qs_is_installed:
        circuit = Circuit.from_string(cqasm_string)
        exported_schedule, _ = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        _check_ref_schedulables(exported_schedule, expected_ref_schedulable_indices)
        _check_waiting_cycles(exported_schedule, expected_waiting_cycles)


def test_control_instruction_stress_test(
    qs_is_installed: bool,
) -> None:
    if qs_is_installed:
        circuit = Circuit.from_string(
            """
            version 3

            qubit[15] q; bit[15] b

            init q

            barrier q
            wait(1) q[0]; wait(2) q[1]; wait(3) q[2]; wait(4) q[3]; wait(5) q[4]; wait(1) q[5]; wait(2) q[6]
            wait(3) q[7]; wait(4) q[8]; wait(5) q[9]; wait(1) q[10]; wait(2) q[11]; wait(3) q[12]; wait(4) q[13]
            wait(5) q[14]

            barrier q[0:7]
            X q[0]; X q[1]; X q[2]; X q[3]; X q[4]; X q[5]; X q[6]; X q[7]

            barrier q[8:14]
            CNOT q[8], q[9]; CNOT q[10], q[11]; CNOT q[12], q[13]

            wait(2) q[0]; wait(3) q[1]; wait(4) q[2]; wait(5) q[3]; wait(1) q[4]; wait(2) q[5]; wait(3) q[6]
            wait(4) q[7]; wait(5) q[8]; wait(1) q[9]; wait(2) q[10]; wait(3) q[11]; wait(4) q[12]; wait(5) q[13]
            wait(1) q[14]

            barrier q
            CZ q[0], q[14]; CZ q[1], q[13]; CZ q[2], q[12]; CZ q[3], q[11]; CZ q[4], q[10]

            barrier q[5:9]
            X q[5]; X q[6]; X q[7]; X q[8]; X q[9]

            barrier q
            b = measure q
            """
        )
        expected_ref_schedulable_indices = [
            25,
            25,
            25,
            25,
            25,
            25,
            25,
            25,
            25,
            25,
            25,
            25,
            25,
            25,
            25,
            26,
            26,
            26,
            26,
            26,
            26,
            26,
            26,
            26,
            26,
            26,
            50,
            50,
            50,
            50,
            50,
            50,
            50,
            50,
            50,
            50,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ]
        expected_waiting_cycles = [
            5,
            5,
            5,
            5,
            5,
            5,
            5,
            5,
            5,
            5,
            5,
            5,
            5,
            5,
            5,
            2,
            3,
            4,
            5,
            1,
            2,
            3,
            4,
            5,
            3,
            5,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0,
        ]
        exported_schedule, _ = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        _check_ref_schedulables(exported_schedule, expected_ref_schedulable_indices)
        _check_waiting_cycles(exported_schedule, expected_waiting_cycles)


@pytest.fixture
def mock_qs() -> Generator[MagicMock, None, None]:
    mock_qs = MagicMock()
    sys.modules["quantify_scheduler"] = mock_qs
    sys.modules.pop("opensquirrel.passes.exporter.quantify_scheduler_exporter", None)
    yield mock_qs
    sys.modules.pop("quantify_scheduler", None)
    sys.modules.pop("opensquirrel.passes.exporter.quantify_scheduler_exporter", None)


def test_export(mock_qs: MagicMock) -> None:
    quantify_scheduler_exporter = importlib.import_module("opensquirrel.passes.exporter.quantify_scheduler_exporter")
    from opensquirrel.passes.exporter.quantify_scheduler_exporter import FIXED_POINT_DEG_PRECISION

    builder = CircuitBuilder(3, 3)
    builder.X(0)
    builder.CZ(0, 1)
    builder.reset(0)
    builder.Rz(1, 2.34)
    builder.Ry(2, 1.23)
    builder.measure(0, 0)
    builder.measure(1, 1)
    builder.measure(2, 2)
    circuit = builder.to_circuit()

    quantify_scheduler_exporter.export(circuit)

    mock_qs.Schedule.assert_called_with("Exported OpenSquirrel circuit")

    mock_qs.operations.gate_library.Rxy.assert_has_calls(
        [
            unittest.mock.call(theta=FloatEq(degrees(pi)), phi=FloatEq(0), qubit="q[0]"),
            unittest.mock.call(
                theta=FloatEq(round(degrees(1.23), FIXED_POINT_DEG_PRECISION)),
                phi=FloatEq(degrees(pi / 2)),
                qubit="q[2]",
            ),
        ]
    )
    mock_qs.operations.gate_library.Reset.assert_called_once_with("q[0]")
    mock_qs.operations.gate_library.CZ.assert_called_once_with(qC="q[0]", qT="q[1]")
    mock_qs.operations.gate_library.Rz.assert_called_once_with(
        theta=FloatEq(round(degrees(2.34), FIXED_POINT_DEG_PRECISION)),
        qubit="q[1]",
    )


@pytest.mark.parametrize(
    "gate",
    [BlochSphereRotation(qubit=0, axis=(1, 2, 3), angle=0.9876, phase=2.34)],
    ids=["BSR"],
)
def test_gates_not_supported(gate: Gate) -> None:
    quantify_scheduler_exporter = importlib.import_module("opensquirrel.passes.exporter.quantify_scheduler_exporter")

    builder = CircuitBuilder(3)
    builder.ir.add_gate(gate)  # or parameterize as before
    circuit = builder.to_circuit()

    with pytest.raises(ExporterError, match="cannot export circuit: "):
        quantify_scheduler_exporter.export(circuit)


def test_quantify_scheduler_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulate quantify_scheduler not being installed
    monkeypatch.setitem(sys.modules, "quantify_scheduler", None)
    sys.modules.pop("opensquirrel.passes.exporter.quantify_scheduler_exporter", None)

    empty_circuit = CircuitBuilder(1).to_circuit()

    with pytest.raises(
        ModuleNotFoundError,
        match="quantify-scheduler is not installed, or cannot be installed on your system",
    ):
        quantify_scheduler_exporter = importlib.import_module(
            "opensquirrel.passes.exporter.quantify_scheduler_exporter"
        )
        quantify_scheduler_exporter.export(empty_circuit)
