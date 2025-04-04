from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from opensquirrel.circuit import Circuit
from opensquirrel.common import ATOL
from opensquirrel.exceptions import ExporterError, UnsupportedGateError
from opensquirrel.ir import (
    CNOT,
    CR,
    CZ,
    SWAP,
    Barrier,
    BlochSphereRotation,
    BsrAngleParam,
    BsrFullParams,
    BsrNoParams,
    ControlledGate,
    CRk,
    Init,
    IRVisitor,
    MatrixGate,
    Measure,
    Reset, Wait,
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


FIXED_POINT_DEG_PRECISION = 5   # Radian to degree conversion outcome precision
CYCLE_TIME = 20e-9              # Operation cycle time (set at 20ns)

class OperationRecord:
    qubit_register_size: int
    ref_operation_ids: list[str]
    operation_counters: list[int]

    def __init__(self, qubit_register_size: int) -> None:
        self.operation_counters = [0] * qubit_register_size
        self.ref_operation_ids = [""] * qubit_register_size
        self._barrier_record: list[Qubit] = []
        self._wait_record: dict[int, int] = {}

    @property
    def barrier_record(self) -> list[Qubit]:
        return self._barrier_record

    @barrier_record.setter
    def barrier_record(self, value: list[Qubit]) -> None:
        self._barrier_record = value

    @property
    def wait_record(self) -> dict[int, int]:
        return self._wait_record

    @wait_record.setter
    def wait_record(self, value: dict[int, int]) -> None:
        self._wait_record = value

    def get_operation_params(self, name: str, qubits: list[Qubit]) -> dict[str, str]:
        self._process_barriers()
        operands = "q" + ", q".join([str(qubit.index) for qubit in qubits])
        operation_id = "{} {}: ".format(name, operands) + str(uuid4())
        operation_counts = [self.operation_counters[qubit.index] for qubit in qubits]
        ref_qubit_index = qubits[self._get_index_of_max_value(operation_counts)].index
        ref_operation_id = self.ref_operation_ids[ref_qubit_index]

        waiting_times: list[int] = []
        for qubit in qubits:
            self.operation_counters[qubit.index] = self.operation_counters[ref_qubit_index] + 1
            self.ref_operation_ids[qubit.index] = operation_id
            if qubit.index in self.wait_record.keys():
                waiting_times.append(self.wait_record[qubit.index])
                del self.wait_record[qubit.index]

        params = {"label": operation_id}
        if not ref_operation_id:
            params["ref_pt"] = "start"
        else:
            params["ref_op"] = ref_operation_id
            params["ref_pt"] = "end"
            params["ref_pt_new"] = "start"
        if waiting_times:
            params["rel_time"] = max(waiting_times) * CYCLE_TIME
        return params

    def _process_barriers(self) -> None:
        if self.barrier_record:
            counters = [self.operation_counters[qubit.index] for qubit in self.barrier_record]
            ref_qubit_index = self.barrier_record[self._get_index_of_max_value(counters)].index
            ref_operation_id = self.ref_operation_ids[ref_qubit_index]
            for qubit in self.barrier_record:
                if qubit.index == ref_qubit_index:
                    continue
                self.ref_operation_ids[qubit.index] = ref_operation_id
            self._barrier_record = []

    @staticmethod
    def _get_index_of_max_value(input_list: list[int]) -> int:
        return max(range(len(input_list)), key=input_list.__getitem__)


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
        operation_params = self.operation_record.get_operation_params(
            gate.name + f"({gate.angle:.2f})",
            gate.get_qubit_operands()
        )
        if abs(gate.axis[2]) < ATOL:
            # Rxy rotation.
            theta = round(math.degrees(gate.angle), FIXED_POINT_DEG_PRECISION)
            phi: float = round(math.degrees(math.atan2(gate.axis[1], gate.axis[0])), FIXED_POINT_DEG_PRECISION)

            self.schedule.add(
                quantify_scheduler_gates.Rxy(theta=theta, phi=phi, qubit=self._get_qubit_string(gate.qubit)),
                **operation_params,
            )
            return

        if abs(gate.axis[0]) < ATOL and abs(gate.axis[1]) < ATOL:
            # Rz rotation.
            theta = round(math.degrees(gate.angle), FIXED_POINT_DEG_PRECISION)
            self.schedule.add(
                quantify_scheduler_gates.Rz(theta=theta, qubit=self._get_qubit_string(gate.qubit)), **operation_params
            )
            return

        raise UnsupportedGateError(gate)

    def visit_bsr_no_params(self, gate: BsrNoParams) -> None:
        self.visit_bloch_sphere_rotation(gate)

    def visit_bsr_full_params(self, gate: BsrFullParams) -> None:
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
        operation_params = self.operation_record.get_operation_params(gate.name, gate.get_qubit_operands())
        self.schedule.add(
            quantify_scheduler_gates.CNOT(
                qC=self._get_qubit_string(gate.control_qubit),
                qT=self._get_qubit_string(gate.target_qubit),
            ),
            **operation_params,
        )
        return

    def visit_cz(self, gate: CZ) -> None:
        operation_params = self.operation_record.get_operation_params(gate.name, gate.get_qubit_operands())
        self.schedule.add(
            quantify_scheduler_gates.CZ(
                qC=self._get_qubit_string(gate.control_qubit),
                qT=self._get_qubit_string(gate.target_qubit),
            ),
            **operation_params,
        )
        return

    def visit_cr(self, gate: CR) -> None:
        raise UnsupportedGateError(gate)

    def visit_crk(self, gate: CRk) -> None:
        raise UnsupportedGateError(gate)

    def visit_measure(self, gate: Measure) -> None:
        operation_params = self.operation_record.get_operation_params(gate.name, gate.get_qubit_operands())
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
            **operation_params,
        )
        self.acq_index_record[qubit_index] += 1
        return

    def visit_init(self, gate: Init) -> None:
        self.visit_reset(cast("Reset", gate))

    def visit_reset(self, gate: Reset) -> None:
        operation_params = self.operation_record.get_operation_params(gate.name, gate.get_qubit_operands())
        self.schedule.add(quantify_scheduler_gates.Reset(self._get_qubit_string(gate.qubit)), **operation_params)
        return

    def visit_barrier(self, gate: Barrier) -> None:
        self.operation_record.barrier_record.append(gate.qubit)

    def visit_wait(self, gate: Wait) -> None:
        self.operation_record.wait_record[gate.qubit.index] = gate.time.value


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
