from __future__ import annotations

import contextlib
import importlib.util
import math
import unittest.mock
from math import isclose
from typing import Any

import pytest

from opensquirrel import CircuitBuilder, H
from opensquirrel.common import ATOL
from opensquirrel.exceptions import ExporterError
from opensquirrel.ir import BlochSphereRotation, Gate


class FloatEq(float):
    def __eq__(self, other: Any) -> bool:
        return isclose(self, other, abs_tol=ATOL)


class MockedQuantifyScheduler:
    def __enter__(self) -> tuple[Any, Any]:
        self.patch_qs = unittest.mock.patch(
            "opensquirrel.passes.exporter.quantify_scheduler_exporter.quantify_scheduler",
            create=True,
        )

        self.patch_qs_gates = unittest.mock.patch(
            "opensquirrel.passes.exporter.quantify_scheduler_exporter.quantify_scheduler_gates",
            create=True,
        )

        with contextlib.ExitStack() as stack:
            self.mock_quantify_scheduler = stack.enter_context(self.patch_qs)
            self.mock_quantify_scheduler_gates = stack.enter_context(self.patch_qs_gates)
            self._stack = stack.pop_all()

        return self.mock_quantify_scheduler, self.mock_quantify_scheduler_gates

    def __exit__(self, exc_type: Any, exc_value: Any, exc_traceback: Any) -> None:
        self._stack.__exit__(exc_type, exc_value, exc_traceback)


class TestQuantifySchedulerExporter:
    def test_export(self) -> None:
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

        with MockedQuantifyScheduler() as (mock_quantify_scheduler, mock_quantify_scheduler_gates):
            from opensquirrel.passes.exporter import quantify_scheduler_exporter
            from opensquirrel.passes.exporter.quantify_scheduler_exporter import FIXED_POINT_DEG_PRECISION

            mock_schedule = unittest.mock.MagicMock()
            mock_quantify_scheduler.Schedule.return_value = mock_schedule
            quantify_scheduler_exporter.export(circuit)

            mock_quantify_scheduler.Schedule.assert_called_with("Exported OpenSquirrel circuit")

            mock_quantify_scheduler_gates.Rxy.assert_has_calls(
                [
                    unittest.mock.call(theta=FloatEq(math.degrees(math.pi)), phi=FloatEq(0), qubit="q[0]"),
                    unittest.mock.call(
                        theta=FloatEq(round(math.degrees(1.23), FIXED_POINT_DEG_PRECISION)),
                        phi=FloatEq(math.degrees(math.pi / 2)),
                        qubit="q[2]",
                    ),
                ],
            )
            mock_quantify_scheduler_gates.Reset.assert_called_once_with("q[0]")
            mock_quantify_scheduler_gates.CZ.assert_called_once_with(qC="q[0]", qT="q[1]")
            mock_quantify_scheduler_gates.Rz.assert_called_once_with(
                theta=FloatEq(round(math.degrees(2.34), FIXED_POINT_DEG_PRECISION)),
                qubit="q[1]",
            )
            assert mock_schedule.add.call_count == 8

    @pytest.mark.parametrize(
        "gate",
        [H(0), BlochSphereRotation(qubit=0, axis=(1, 2, 3), angle=0.9876, phase=2.34)],
        ids=["H", "BSR"],
    )
    def test_gates_not_supported(self, gate: Gate) -> None:
        builder = CircuitBuilder(3)
        builder.ir.add_gate(gate)
        circuit = builder.to_circuit()

        with MockedQuantifyScheduler(), pytest.raises(ExporterError, match="cannot export circuit: "):
            from opensquirrel.passes.exporter import quantify_scheduler_exporter

            quantify_scheduler_exporter.export(circuit)


@pytest.mark.skipif(
    importlib.util.find_spec("quantify_scheduler") is not None,
    reason="quantify_scheduler is installed",
)
def test_quantify_scheduler_not_installed() -> None:
    empty_circuit = CircuitBuilder(1).to_circuit()
    with pytest.raises(
        ModuleNotFoundError,
        match="quantify-scheduler is not installed, or cannot be installed on your system",
    ):
        from opensquirrel.passes.exporter import quantify_scheduler_exporter

        quantify_scheduler_exporter.export(empty_circuit)
