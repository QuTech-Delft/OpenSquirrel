from __future__ import annotations

import importlib
import sys
import unittest.mock
from collections.abc import Generator
from math import degrees, isclose, pi
from typing import Any
from unittest.mock import MagicMock

import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.common import ATOL
from opensquirrel.exceptions import ExporterError
from opensquirrel.ir import BlochSphereRotation, Gate, H


class FloatEq(float):
    def __eq__(self, other: Any) -> bool:
        return isclose(self, other, abs_tol=ATOL)


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
    [H(0), BlochSphereRotation(qubit=0, axis=(1, 2, 3), angle=0.9876, phase=2.34)],
    ids=["H", "BSR"],
)
def test_gates_not_supported(mock_qs: MagicMock, gate: Gate) -> None:
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
