from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opensquirrel.default_gates import X, Z
from opensquirrel.exceptions import ExporterError, UnsupportedGateError
from opensquirrel.ir import BlochSphereRotation, ControlledGate, IRVisitor, MatrixGate, Measure, Qubit, Reset

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit


class _CQASMv1Creator(IRVisitor):
    def _get_qubit_string(self, q: Qubit) -> str:
        return f"{self.qubit_register_name}[{q.index}]"

    def __init__(self, qubit_register_name: str) -> None:
        self.qubit_register_name = qubit_register_name
        self.cqasmv1_string = "version 1.0\n\n"

    def visit_bloch_sphere_rotation(self, g: BlochSphereRotation) -> None:
        # Note that when adding a rotation gate to the Quantify-scheduler Schedule,
        # there exists an ambiguity with how Quantify-scheduler will store an angle of 180 degrees.
        # Depending on the system the angle may be stored as either 180 or -180 degrees.
        # This ambiguity has no physical consequences, but may cause the exporter test fail.
        # if g is recognized:
        #     ...
        #     return
        #
        # raise UnsupportedGateError(g)

    def visit_matrix_gate(self, g: MatrixGate) -> None:
        raise UnsupportedGateError(g)

    def visit_controlled_gate(self, g: ControlledGate) -> None:
        if not isinstance(g.target_gate, BlochSphereRotation):
            raise UnsupportedGateError(g)

        if g.target_gate == X(g.target_gate.qubit):
            # check if anything special needs to be done.
                    #self._get_qubit_string(g.control_qubit),
                    #self._get_qubit_string(g.target_gate.qubit),
            # return
            return

        if g.target_gate == Z(g.target_gate.qubit):
            # check if anything special needs to be done.
            # self._get_qubit_string(g.control_qubit),
            # self._get_qubit_string(g.target_gate.qubit),
            # return
            return

        raise UnsupportedGateError(g)

    def visit_measure(self, g: Measure) -> None:
        # remove the bit variable
        pass

    def visit_reset(self, g: Reset) -> Any:
        # turn into prep_z?
        pass


def export(circuit: Circuit) -> str:

    cqasmv1_creator = _CQASMv1Creator(circuit.qubit_register_name)
    try:
        circuit.ir.accept(cqasmv1_creator)
    except UnsupportedGateError as e:
        msg = (
            f"cannot export circuit: {e}."
        )
        raise ExporterError(msg) from e
    return cqasmv1_creator.cqasmv1_string
