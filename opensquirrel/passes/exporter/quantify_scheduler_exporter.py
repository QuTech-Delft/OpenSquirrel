from __future__ import annotations

import math
from dataclasses import dataclass, InitVar, field
from typing import TYPE_CHECKING, Any

from opensquirrel.circuit import Circuit
from opensquirrel.common import ATOL
from opensquirrel.exceptions import ExporterError, UnsupportedGateError
from opensquirrel.ir import (
    CNOT,
    CR,
    CZ,
    SWAP,
    BlochSphereRotation,
    BsrAngleParam,
    BsrNoParams,
    ControlledGate,
    CRk,
    IRVisitor,
    MatrixGate,
    Measure,
    Reset, Barrier, Init
)

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


class OperationRecord:

    qubit_register_size: int
    operation_ids: list[str]
    operation_counters: list[int]
    operation_count: int = 0

    def __init__(self, qubit_register_size):
        self.operation_counters = [0] * qubit_register_size
        self.operation_ids = [""] * qubit_register_size
        self._barrier_record: list[int] = []

    @property
    def barrier_record(self) -> list[int]:
        return self._barrier_record

    @barrier_record.setter
    def barrier_record(self, value):
        self._barrier_record = value

    def update(self, indices: list[int], operation_id: str) -> None:
        for index in indices:
            self.operation_counters[index] = self.operation_count
            self.operation_ids[index] = operation_id
        self.operation_count += 1

    def get_operation_reference(self, indices: list[int]) -> dict[str, str]:
        self._process_barriers()
        operation_counts = [self.operation_counters[index] for index in indices]
        index = indices[operation_counts.index(max(operation_counts))]
        operation_id = self.operation_ids[index]
        if not operation_id:
            return {"ref_pt": "start"}
        return {"ref_op": operation_id}

    def _process_barriers(self) -> None:
        if self.barrier_record:
            counters = [self.operation_counters[index] for index in self.barrier_record]
            index = self.barrier_record[counters.index(max(counters))]
            operation_id = self.operation_ids[index]
            for barrier_index in self.barrier_record:
                if barrier_index == index:
                    continue
                self.operation_ids[barrier_index] = operation_id
            self._barrier_record = []


class _ScheduleCreator(IRVisitor):
    def _get_qubit_string(self, qubit: Qubit) -> str:
        return f"{self.qubit_register_name}[{qubit.index}]"

    def __init__(self, register_manager: RegisterManager) -> None:
        self.register_manager = register_manager
        self.qubit_register_size = register_manager.get_qubit_register_size()
        self.qubit_register_name = register_manager.get_qubit_register_name()
        self.bit_register_size = register_manager.get_bit_register_size()
        self.operation_record = OperationRecord(self.qubit_register_size)
        self.acq_index_record = [0] * self.qubit_register_size
        self.bit_string_mapping: list[tuple[None, None] | tuple[int, int]] = [(None, None)] * self.bit_register_size
        self.schedule = quantify_scheduler.Schedule("Exported OpenSquirrel circuit")

    def visit_bloch_sphere_rotation(self, gate: BlochSphereRotation) -> None:
        # Note that when adding a rotation gate to the Quantify-scheduler Schedule,
        # there exists an ambiguity with how Quantify-scheduler will store an angle of 180 degrees.
        # Depending on the system the angle may be stored as either 180 or -180 degrees.
        # This ambiguity has no physical consequences, but may cause the exporter test fail.
        reference_param = self.operation_record.get_operation_reference([gate.qubit.index])
        if abs(gate.axis[2]) < ATOL:
            # Rxy rotation.
            theta = round(math.degrees(gate.angle), FIXED_POINT_DEG_PRECISION)
            phi: float = round(math.degrees(math.atan2(gate.axis[1], gate.axis[0])), FIXED_POINT_DEG_PRECISION)

            self.schedule.add(
                quantify_scheduler_gates.Rxy(theta=theta, phi=phi, qubit=self._get_qubit_string(gate.qubit)),
                **reference_param
            )
            self.operation_record.update([gate.qubit.index], [*self.schedule.schedulables][-1])
            return

        if abs(gate.axis[0]) < ATOL and abs(gate.axis[1]) < ATOL:
            # Rz rotation.
            theta = round(math.degrees(gate.angle), FIXED_POINT_DEG_PRECISION)
            self.schedule.add(quantify_scheduler_gates.Rz(theta=theta, qubit=self._get_qubit_string(gate.qubit)),
                              **reference_param
                              )
            self.operation_record.update([gate.qubit.index], [*self.schedule.schedulables][-1])
            return

        raise UnsupportedGateError(gate)

    def visit_bsr_no_params(self, gate: BsrNoParams) -> None:
        self.visit_bloch_sphere_rotation(gate)

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> None:
        self.visit_bloch_sphere_rotation(gate)

    def visit_matrix_gate(self, gate: MatrixGate) -> None:
        raise UnsupportedGateError(gate)

    def visit_swap(self, gate: SWAP) -> None:
        raise UnsupportedGateError(gate)

    def visit_controlled_gate(self, gate: ControlledGate) -> None:
        if not isinstance(gate.target_gate, BlochSphereRotation):
            raise UnsupportedGateError(gate)

    def visit_cnot(self, gate: CNOT) -> None:
        reference_param = self.operation_record.get_operation_reference(
            [gate.control_qubit.index, gate.target_qubit.index])
        self.schedule.add(
            quantify_scheduler_gates.CNOT(
                qC=self._get_qubit_string(gate.control_qubit),
                qT=self._get_qubit_string(gate.target_qubit),
            ),
            **reference_param
        )
        self.operation_record.update([gate.control_qubit.index, gate.target_qubit.index], [*self.schedule.schedulables][-1])
        return

    def visit_cz(self, gate: CZ) -> None:
        reference_param = self.operation_record.get_operation_reference([gate.control_qubit.index, gate.target_qubit.index])
        self.schedule.add(
            quantify_scheduler_gates.CZ(
                qC=self._get_qubit_string(gate.control_qubit),
                qT=self._get_qubit_string(gate.target_qubit),
            ),
            **reference_param
        )
        self.operation_record.update([gate.control_qubit.index, gate.target_qubit.index], [*self.schedule.schedulables][-1])
        return

    def visit_cr(self, gate: CR) -> None:
        raise UnsupportedGateError(gate)

    def visit_crk(self, gate: CRk) -> None:
        raise UnsupportedGateError(gate)

    def visit_measure(self, gate: Measure) -> None:
        reference_param = self.operation_record.get_operation_reference([gate.qubit.index])
        qubit_index = gate.qubit.index
        bit_index = gate.bit.index
        acq_index = self.acq_index_record[qubit_index]
        self.bit_string_mapping[bit_index] = (acq_index, qubit_index)
        self.schedule.add(
            quantify_scheduler_gates.Measure(
                self._get_qubit_string(gate.qubit),
                acq_channel=qubit_index,
                acq_index=acq_index,
                acq_protocol="ThresholdedAcquisition",
            ),
            **reference_param
        )
        self.acq_index_record[qubit_index] += 1
        self.operation_record.update([gate.qubit.index], [*self.schedule.schedulables][-1])
        return

    def visit_init(self, gate: Init) -> None:
        reference_param = self.operation_record.get_operation_reference([gate.qubit.index])
        self.schedule.add(quantify_scheduler_gates.Reset(self._get_qubit_string(gate.qubit)),
                          **reference_param)
        self.operation_record.update([gate.qubit.index], [*self.schedule.schedulables][-1])
        return

    def visit_reset(self, gate: Reset) -> None:
        reference_param = self.operation_record.get_operation_reference([gate.qubit.index])
        self.schedule.add(quantify_scheduler_gates.Reset(self._get_qubit_string(gate.qubit)),
                          **reference_param)
        self.operation_record.update([gate.qubit.index], [*self.schedule.schedulables][-1])
        return

    def visit_barrier(self, gate: Barrier) -> None:
        self.operation_record.barrier_record.append(gate.qubit.index)


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
