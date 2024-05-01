import math

from opensquirrel.circuit import Circuit
from opensquirrel.common import ATOL
from opensquirrel.default_gates import X, Z
from opensquirrel.squirrel_ir import BlochSphereRotation, ControlledGate, MatrixGate, Qubit, SquirrelIRVisitor

try:
    import quantify_scheduler
    import quantify_scheduler.operations.gate_library as quantify_scheduler_gates
except Exception as e:
    pass


_unsupported_gates_exception = Exception(
    "Cannot exporter circuit: it contains unsupported gates - decomposer them to the "
    "Quantify-scheduler gate set first (rxy, rz, cnot, cz)"
)


class _ScheduleCreator(SquirrelIRVisitor):
    def _get_qubit_string(self, q: Qubit) -> str:
        return f"{self.qubit_register_name}[{q.index}]"

    def __init__(self, qubit_register_name: str):
        self.qubit_register_name = qubit_register_name
        self.schedule = quantify_scheduler.Schedule("Exported OpenSquirrel circuit")

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation):
        if abs(g.axis[2]) < ATOL:
            # Rxy rotation.
            theta: float = math.degrees(g.angle)
            phi: float = math.degrees(math.atan2(g.axis[1], g.axis[0]))
            self.schedule.add(quantify_scheduler_gates.Rxy(theta=theta, phi=phi, qubit=self._get_qubit_string(g.qubit)))
            return

        if abs(g.axis[0]) < ATOL and abs(g.axis[1]) < ATOL:
            # Rz rotation.
            theta: float = math.degrees(g.angle)
            self.schedule.add(quantify_scheduler_gates.Rz(theta=theta, qubit=self._get_qubit_string(g.qubit)))
            return

        raise _unsupported_gates_exception

    def visit_matrix_gate(self, g: MatrixGate):
        raise _unsupported_gates_exception

    def visit_controlled_gate(self, g: ControlledGate):
        if not isinstance(g.target_gate, BlochSphereRotation):
            raise _unsupported_gates_exception

        if g.target_gate == X(g.target_gate.qubit):
            self.schedule.add(
                quantify_scheduler_gates.CNOT(
                    qC=self._get_qubit_string(g.control_qubit), qT=self._get_qubit_string(g.target_gate.qubit)
                )
            )
            return

        if g.target_gate == Z(g.target_gate.qubit):
            self.schedule.add(
                quantify_scheduler_gates.CZ(
                    qC=self._get_qubit_string(g.control_qubit), qT=self._get_qubit_string(g.target_gate.qubit)
                )
            )
            return

        raise _unsupported_gates_exception


def export(circuit: Circuit):
    if "quantify_scheduler" not in globals():

        class QuantifySchedulerNotInstalled:
            def __getattr__(self, attr_name):
                raise ImportError("quantify-scheduler is not installed, or cannot be installed on your system")

        global quantify_scheduler
        quantify_scheduler = QuantifySchedulerNotInstalled()
        global quantify_scheduler_gates
        quantify_scheduler_gates = QuantifySchedulerNotInstalled()

    schedule_creator = _ScheduleCreator(circuit.qubit_register_name)
    circuit.squirrel_ir.accept(schedule_creator)
    return schedule_creator.schedule
