from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from opensquirrel import X, Z
from opensquirrel.circuit import Circuit
from opensquirrel.common import ATOL
from opensquirrel.exceptions import ExporterError, UnsupportedGateError
from opensquirrel.ir import BlochSphereRotation, ControlledGate, IRVisitor, MatrixGate, Measure, Reset

try:
    import quantify_scheduler
    import quantify_scheduler.operations.gate_library as quantify_scheduler_gates
except ModuleNotFoundError:
    pass

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit
    from opensquirrel.ir import Qubit
    from opensquirrel.register_manager import RegisterManager

# Radian to degree conversion outcome precision
FIXED_POINT_DEG_PRECISION = 5


class _ScheduleCreator(IRVisitor):
    def _get_qubit_string(self, q: Qubit) -> str:
        return f"{self.qubit_register_name}[{q.index}]"

    def __init__(self, register_manager: RegisterManager) -> None:
        self.register_manager = register_manager
        self.qubit_register_size = register_manager.get_qubit_register_size()
        self.qubit_register_name = register_manager.get_qubit_register_name()
        self.bit_register_size = register_manager.get_bit_register_size()
        self.acq_index_record = [0] * self.qubit_register_size
        self.bit_string_mapping: list[tuple[None, None] | tuple[int, int]] = [(None, None)] * self.bit_register_size
        self.schedule = quantify_scheduler.Schedule("Exported OpenSquirrel circuit")

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation) -> None:
        # Note that when adding a rotation gate to the Quantify-scheduler Schedule,
        # there exists an ambiguity with how Quantify-scheduler will store an angle of 180 degrees.
        # Depending on the system the angle may be stored as either 180 or -180 degrees.
        # This ambiguity has no physical consequences, but may cause the exporter test fail.
        if abs(g.axis[2]) < ATOL:
            # Rxy rotation.
            theta = round(math.degrees(g.angle), FIXED_POINT_DEG_PRECISION)
            phi: float = round(math.degrees(math.atan2(g.axis[1], g.axis[0])), FIXED_POINT_DEG_PRECISION)
            self.schedule.add(quantify_scheduler_gates.Rxy(theta=theta, phi=phi, qubit=self._get_qubit_string(g.qubit)))
            return

        if abs(g.axis[0]) < ATOL and abs(g.axis[1]) < ATOL:
            # Rz rotation.
            theta = round(math.degrees(g.angle), FIXED_POINT_DEG_PRECISION)
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

    def visit_measure(self, g: Measure) -> None:
        qubit_index = g.qubit.index
        bit_index = g.bit.index
        acq_index = self.acq_index_record[qubit_index]
        self.bit_string_mapping[bit_index] = (acq_index, qubit_index)
        self.schedule.add(
            quantify_scheduler_gates.Measure(
                self._get_qubit_string(g.qubit),
                acq_channel=qubit_index,
                acq_index=acq_index,
                acq_protocol="ThresholdedAcquisition",
            )
        )
        self.acq_index_record[qubit_index] += 1
        return

    def visit_reset(self, g: Reset) -> Any:
        self.schedule.add(quantify_scheduler_gates.Reset(self._get_qubit_string(g.qubit)))


def export(circuit: Circuit) -> tuple[quantify_scheduler.Schedule, list[tuple[Any, Any]]]:
    if "quantify_scheduler" not in globals():

        class QuantifySchedulerNotInstalled:
            def __getattr__(self, attr_name: Any) -> None:
                msg = "quantify-scheduler is not installed, or cannot be installed on your system"
                raise ModuleNotFoundError(msg)

        global quantify_scheduler
        quantify_scheduler = QuantifySchedulerNotInstalled()
        global quantify_scheduler_gates
        quantify_scheduler_gates = QuantifySchedulerNotInstalled()

    schedule_creator = _ScheduleCreator(circuit.register_manager)
    try:
        circuit.ir.accept(schedule_creator)
    except UnsupportedGateError as e:
        msg = (
            f"cannot export circuit: {e}. "
            "Decompose all gates to the Quantify-scheduler gate set first (rxy, rz, cnot, cz)"
        )
        raise ExporterError(msg) from e
    return schedule_creator.schedule, schedule_creator.bit_string_mapping
