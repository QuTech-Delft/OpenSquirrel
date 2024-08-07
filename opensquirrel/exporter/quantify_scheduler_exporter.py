from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from opensquirrel.common import ATOL
from opensquirrel.default_gates import X, Z
from opensquirrel.exceptions import ExporterError, UnsupportedGateError
from opensquirrel.ir import (
    BlochSphereRotation,
    ControlledGate,
    IRVisitor,
    MatrixGate,
    Measure,
    Qubit,
)

try:
    import quantify_scheduler
    import quantify_scheduler.operations.gate_library as quantify_scheduler_gates
except ModuleNotFoundError:
    pass

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit


# Radian to degree conversion outcome precision
DEG_PRECISION = 5


class _ScheduleCreator(IRVisitor):
    def _get_qubit_string(self, q: Qubit) -> str:
        return f"{self.qubit_register_name}[{q.index}]"

    def __init__(self, qubit_register_name: str) -> None:
        self.qubit_register_name = qubit_register_name
        self.schedule = quantify_scheduler.Schedule("Exported OpenSquirrel circuit")

    def visit_measure(self, g: Measure) -> None:
        self.schedule.add(
            quantify_scheduler_gates.Measure(
                self._get_qubit_string(g.qubit),
                acq_channel=g.qubit.index,
                acq_index=g.qubit.index,
                acq_protocol="ThresholdedAcquisition",
            ),
        )

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation) -> None:
        # Note that when adding a rotation gate to the Quantify-scheduler Schedule,
        # there exists an ambiguity with how Quantify-scheduler will store an angle of 180 degrees.
        # Depending on the system the angle may be stored as either 180 or -180 degrees.
        # This ambiguity has no physical consequences, but may cause the exporter test fail.
        if abs(g.axis[2]) < ATOL:
            # Rxy rotation.
            theta = round(math.degrees(g.angle), DEG_PRECISION)
            phi: float = round(math.degrees(math.atan2(g.axis[1], g.axis[0])), DEG_PRECISION)
            self.schedule.add(quantify_scheduler_gates.Rxy(theta=theta, phi=phi, qubit=self._get_qubit_string(g.qubit)))
            return

        if abs(g.axis[0]) < ATOL and abs(g.axis[1]) < ATOL:
            # Rz rotation.
            theta = round(math.degrees(g.angle), DEG_PRECISION)
            self.schedule.add(quantify_scheduler_gates.Rz(theta=theta, qubit=self._get_qubit_string(g.qubit)))
            return

        raise UnsupportedGateError(g)

    def visit_matrix_gate(self, g: MatrixGate) -> None:
        raise UnsupportedGateError(g)

    def visit_controlled_gate(self, g: ControlledGate) -> None:
        if not isinstance(g.target_gate, BlochSphereRotation):
            raise UnsupportedGateError(g)

        if g.target_gate == X(g.target_gate.qubit):
            self.schedule.add(
                quantify_scheduler_gates.CNOT(
                    qC=self._get_qubit_string(g.control_qubit),
                    qT=self._get_qubit_string(g.target_gate.qubit),
                ),
            )
            return

        if g.target_gate == Z(g.target_gate.qubit):
            self.schedule.add(
                quantify_scheduler_gates.CZ(
                    qC=self._get_qubit_string(g.control_qubit),
                    qT=self._get_qubit_string(g.target_gate.qubit),
                ),
            )
            return

        raise UnsupportedGateError(g)


def export(circuit: Circuit) -> quantify_scheduler.Schedule:
    if "quantify_scheduler" not in globals():

        class QuantifySchedulerNotInstalled:
            def __getattr__(self, attr_name: Any) -> None:
                msg = "quantify-scheduler is not installed, or cannot be installed on your system"
                raise ModuleNotFoundError(msg)

        global quantify_scheduler
        quantify_scheduler = QuantifySchedulerNotInstalled()
        global quantify_scheduler_gates
        quantify_scheduler_gates = QuantifySchedulerNotInstalled()

    schedule_creator = _ScheduleCreator(circuit.qubit_register_name)
    try:
        circuit.ir.accept(schedule_creator)
    except UnsupportedGateError as e:
        msg = (
            f"cannot export circuit: {e}. "
            "Decompose all gates to the Quantify-scheduler gate set first (rxy, rz, cnot, cz)"
        )
        raise ExporterError(msg) from e
    return schedule_creator.schedule
