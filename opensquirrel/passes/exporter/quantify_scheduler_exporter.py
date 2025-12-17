from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

from opensquirrel import Init, Measure, Reset, Wait
from opensquirrel.common import ATOL
from opensquirrel.exceptions import ExporterError, UnsupportedGateError
from opensquirrel.ir import (
    ControlInstruction,
    Gate,
    IRVisitor,
    NonUnitary,
)
from opensquirrel.passes.exporter.general_exporter import Exporter

try:
    import quantify_scheduler
    from quantify_scheduler.schedules import Schedulable  # noqa: TC002
    from quantify_scheduler.schedules.schedule import TimingConstraint
except ModuleNotFoundError:
    pass

if TYPE_CHECKING:
    from opensquirrel import Circuit
    from opensquirrel.ir import Qubit
    from opensquirrel.ir.single_qubit_gate import SingleQubitGate
    from opensquirrel.ir.two_qubit_gate import TwoQubitGate
    from opensquirrel.register_manager import RegisterManager

OperationCycles = dict[str, int]

CYCLE_TIME = 20e-9  # Operation cycle time (set at 20 [ns]).
DEFAULT_OPERATION_CYCLES = 1  # An operation takes 1 operation cycle by default.
FIXED_POINT_DEG_PRECISION = 5  # Radian to degree conversion outcome precision.


class QuantifySchedulerExporter(Exporter):
    def __init__(self, operation_cycles: OperationCycles | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._operation_cycles = operation_cycles

    def export(self, circuit: Circuit) -> tuple[quantify_scheduler.Schedule, list[tuple[Any, Any]]]:
        if "quantify_scheduler" not in globals():

            class QuantifySchedulerNotInstalled:
                def __getattr__(self, attr_name: Any) -> None:
                    msg = "quantify-scheduler is not installed, or cannot be installed on your system"
                    raise ModuleNotFoundError(msg)

            global quantify_scheduler
            quantify_scheduler = QuantifySchedulerNotInstalled()

        try:
            # Create circuit, with measure data
            schedule_creator = _ScheduleCreator(circuit.register_manager)
            circuit.ir.accept(schedule_creator)

            # Obtain ALAP reference timing for schedulables
            schedulables = list(schedule_creator.schedule.schedulables.values())
            if schedulables:
                scheduler = _Scheduler(circuit.register_manager, schedulables, self._operation_cycles)
                circuit.ir.reverse().accept(scheduler)

                # Update timing constraints of schedulables
                for name, schedulable in schedule_creator.schedule.schedulables.items():
                    schedulable["timing_constraints"] = [
                        scheduler.operation_record.schedulable_timing_constraints[name]
                    ]

        except UnsupportedGateError as e:
            msg = (
                f"cannot export circuit: {e}. "
                "Decompose all gates to the gate set supported by quantify-scheduler first, i.e., "
                "(init, reset, H, Rx, Ry, Rz, CNOT, CZ, measure)"
            )
            raise ExporterError(msg) from e

        return schedule_creator.schedule, schedule_creator.bit_string_mapping


class OperationRecord:
    def __init__(
        self,
        qubit_register_size: int,
        schedulables: list[Schedulable],
        operation_cycles: OperationCycles | None,
    ) -> None:
        self._schedulables = schedulables
        self._operation_cycles = operation_cycles
        self._cycles: list[int] = [0] * qubit_register_size
        self._ref_index: list[int] = list(range(qubit_register_size))
        self._ref_schedulables: list[tuple[Schedulable | None, int]] = list(
            zip([None] * qubit_register_size, [0] * qubit_register_size, strict=False)
        )
        self._barrier_record: list[int] = []
        self._schedulable_timing_constraints: dict[str, TimingConstraint] = {}

    @staticmethod
    def get_index_of_max_value(input_list: list[int]) -> int:
        return max(range(len(input_list)), key=input_list.__getitem__)

    @property
    def schedulable_timing_constraints(self) -> dict[str, TimingConstraint]:
        return self._schedulable_timing_constraints

    def set_schedulable_timing_constraints(self, qubit_indices: list[int]) -> None:
        self._process_barriers()
        schedulable: Schedulable = self._schedulables.pop()
        pertinent_qubit_index, ref_schedulable, ref_cycle = self._get_reference(qubit_indices=qubit_indices)

        operation_cycles = self._get_operation_cycles(schedulable) if ref_schedulable else 0
        cycle = self._cycles[pertinent_qubit_index] + operation_cycles
        waiting_time = -1.0 * ((cycle - operation_cycles) - ref_cycle) * CYCLE_TIME
        self._set_timing_constraints(schedulable, ref_schedulable, waiting_time)

        self._set_reference(qubit_indices, schedulable, cycle)

    def add_qubit_index_to_barrier_record(self, qubit_index: int) -> None:
        if qubit_index not in self._barrier_record:
            self._barrier_record.append(qubit_index)

    def process_wait(self, qubit_index: int, cycles: int) -> None:
        self._process_barriers()
        self._cycles[qubit_index] += cycles

    def _get_reference(self, qubit_indices: list[int]) -> tuple[int, Schedulable, int]:
        schedulable_counts = [self._cycles[qubit_index] for qubit_index in qubit_indices]
        pertinent_qubit_index = qubit_indices[self.get_index_of_max_value(schedulable_counts)]
        ref_schedulable, ref_counter_value = self._ref_schedulables[pertinent_qubit_index]
        return pertinent_qubit_index, ref_schedulable, ref_counter_value

    def _set_reference(self, qubit_indices: list[int], new_ref_schedulable: Schedulable, new_ref_cycle: int) -> None:
        temp_cycles = self._cycles.copy()
        for qubit_index in qubit_indices:
            temp_cycles[qubit_index] = new_ref_cycle
            self._ref_schedulables[qubit_index] = (new_ref_schedulable, new_ref_cycle)
        self._cycles = temp_cycles

    def _set_timing_constraints(
        self, schedulable: Schedulable, ref_schedulable: Schedulable, waiting_time: float
    ) -> None:
        if not ref_schedulable:
            timing_constraint = TimingConstraint(
                ref_schedulable=None,
                ref_pt="end",
                ref_pt_new="end",
                rel_time=0,
            )
        else:
            timing_constraint = TimingConstraint(
                ref_schedulable=ref_schedulable["name"],
                ref_pt="start",
                ref_pt_new="end",
                rel_time=0,
            )
        timing_constraint.rel_time = waiting_time
        self._schedulable_timing_constraints[schedulable["name"]] = timing_constraint

    def _process_barriers(self) -> None:
        if self._barrier_record:
            pertinent_qubit_index, ref_schedulable, ref_cycle = self._get_reference(qubit_indices=self._barrier_record)
            temp_cycles = self._cycles.copy()
            for qubit_index in self._barrier_record:
                temp_cycles[qubit_index] = self._cycles[pertinent_qubit_index]
                self._ref_schedulables[qubit_index] = (ref_schedulable, ref_cycle)
            self._cycles = temp_cycles
            self._barrier_record = []

    def _get_operation_cycles(self, schedulable: Schedulable) -> int:
        if not self._operation_cycles:
            return DEFAULT_OPERATION_CYCLES
        operation_name = schedulable.get("name").split()[0]
        return self._operation_cycles.get(operation_name, DEFAULT_OPERATION_CYCLES)


class _Scheduler(IRVisitor):
    def __init__(
        self,
        register_manager: RegisterManager,
        schedulables: list[Schedulable],
        operation_cycles: OperationCycles | None,
    ) -> None:
        self._qubit_register_size = register_manager.get_qubit_register_size()
        self._operation_cycles = operation_cycles
        self._operation_record = OperationRecord(self._qubit_register_size, schedulables, operation_cycles)

    @property
    def operation_record(self) -> OperationRecord:
        return self._operation_record

    def visit_gate(self, gate: Gate) -> None:
        qubit_indices = [qubit.index for qubit in gate.get_qubit_operands()]
        self._operation_record.set_schedulable_timing_constraints(qubit_indices)

    def visit_non_unitary(self, non_unitary: NonUnitary) -> None:
        qubit_indices = [qubit.index for qubit in non_unitary.get_qubit_operands()]
        self._operation_record.set_schedulable_timing_constraints(qubit_indices)

    def visit_control_instruction(self, control_instruction: ControlInstruction) -> None:
        if isinstance(control_instruction, Wait):
            self._operation_record.process_wait(control_instruction.qubit.index, control_instruction.time.value)
        else:
            self._operation_record.add_qubit_index_to_barrier_record(control_instruction.qubit.index)


class _ScheduleCreator(IRVisitor):
    def __init__(
        self,
        register_manager: RegisterManager,
    ) -> None:
        self.register_manager = register_manager
        self.qubit_register_size = register_manager.get_qubit_register_size()
        self.qubit_register_name = register_manager.get_qubit_register_name()
        self.bit_register_size = register_manager.get_bit_register_size()
        self.acq_index_record = [0] * self.qubit_register_size
        self.bit_string_mapping: list[tuple[None, None] | tuple[int, int]] = [(None, None)] * self.bit_register_size
        self.schedule = quantify_scheduler.Schedule("Exported OpenSquirrel circuit")

    def visit_single_qubit_gate(self, gate: SingleQubitGate) -> None:
        # def visit_bloch_sphere_rotation(self, gate: BlochSphereRotation) -> None:
        # Note that when adding a rotation gate to the Quantify-scheduler Schedule,
        # there exists an ambiguity with how Quantify-scheduler will store an angle of 180 degrees.
        # Depending on the system the angle may be stored as either 180 or -180 degrees.
        # This ambiguity has no physical consequences, but may cause the exporter test fail.
        if (
            abs(gate.bsr.axis[0] - 1 / math.sqrt(2)) < ATOL
            and abs(gate.bsr.axis[1]) < ATOL
            and abs(gate.bsr.axis[2] - 1 / math.sqrt(2)) < ATOL
        ):
            # Hadamard gate.
            self.schedule.add(
                quantify_scheduler.operations.gate_library.H(self._get_qubit_string(gate.qubit)),
                label=self._get_operation_label("H", gate.get_qubit_operands()),
            )
            return
        if abs(gate.bsr.axis[2]) < ATOL:
            # Rxy rotation.
            theta = round(math.degrees(gate.bsr.angle), FIXED_POINT_DEG_PRECISION)
            phi: float = round(math.degrees(math.atan2(gate.bsr.axis[1], gate.bsr.axis[0])), FIXED_POINT_DEG_PRECISION)

            self.schedule.add(
                quantify_scheduler.operations.gate_library.Rxy(
                    theta=theta, phi=phi, qubit=self._get_qubit_string(gate.qubit)
                ),
                label=self._get_operation_label("Rxy", gate.get_qubit_operands()),
            )
            return
        if abs(gate.bsr.axis[0]) < ATOL and abs(gate.bsr.axis[1]) < ATOL:
            # Rz rotation.
            theta = round(math.degrees(gate.bsr.angle), FIXED_POINT_DEG_PRECISION)
            self.schedule.add(
                quantify_scheduler.operations.gate_library.Rz(theta=theta, qubit=self._get_qubit_string(gate.qubit)),
                label=self._get_operation_label("Rz", gate.get_qubit_operands()),
            )
            return
        raise UnsupportedGateError(gate)

    def visit_two_qubit_gate(self, gate: TwoQubitGate) -> Any:
        if gate.name not in ["CNOT", "CZ"]:
            raise UnsupportedGateError(gate)

        control_qubit, target_qubit = gate.get_qubit_operands()

        if gate.name == "CNOT":
            self.schedule.add(
                quantify_scheduler.operations.gate_library.CNOT(
                    qC=self._get_qubit_string(control_qubit),
                    qT=self._get_qubit_string(target_qubit),
                ),
                label=self._get_operation_label("CNOT", gate.get_qubit_operands()),
            )
        if gate.name == "CZ":
            self.schedule.add(
                quantify_scheduler.operations.gate_library.CZ(
                    qC=self._get_qubit_string(control_qubit),
                    qT=self._get_qubit_string(target_qubit),
                ),
                label=self._get_operation_label("CZ", gate.get_qubit_operands()),
            )

    def visit_measure(self, gate: Measure) -> None:
        qubit_index = gate.qubit.index
        bit_index = gate.bit.index
        acq_index = self.acq_index_record[qubit_index]
        self.bit_string_mapping[bit_index] = (acq_index, qubit_index)
        self.schedule.add(
            quantify_scheduler.operations.gate_library.Measure(
                self._get_qubit_string(gate.qubit),
                acq_channel=qubit_index,
                acq_index=acq_index,
                acq_protocol="ThresholdedAcquisition",
            ),
            label=self._get_operation_label("Measure", gate.get_qubit_operands()),
        )
        self.acq_index_record[qubit_index] += 1

    def visit_init(self, gate: Init) -> None:
        self.visit_reset(cast("Reset", gate))

    def visit_reset(self, gate: Reset) -> None:
        self.schedule.add(
            quantify_scheduler.operations.gate_library.Reset(self._get_qubit_string(gate.qubit)),
            label=self._get_operation_label("Reset", gate.get_qubit_operands()),
        )

    def _get_qubit_string(self, qubit: Qubit) -> str:
        return f"{self.qubit_register_name}[{qubit.index}]"

    def _get_operation_label(self, name: str, qubits: list[Qubit]) -> str:
        qubit_operands = ", ".join([self._get_qubit_string(qubit) for qubit in qubits])
        return f"{name} {qubit_operands} | " + str(uuid4())
