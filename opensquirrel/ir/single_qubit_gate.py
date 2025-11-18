from __future__ import annotations

from typing import TYPE_CHECKING, Any

from opensquirrel.ir import Float, Gate, Qubit, QubitLike
from opensquirrel.ir.semantics.bsr import BlochSphereRotation
from opensquirrel.ir.semantics.gate_semantic import GateSemantic, MatrixSemantic

if TYPE_CHECKING:
    from opensquirrel.ir.ir import IRVisitor


def try_match_replace_with_default_gate(gate: SingleQubitGate) -> SingleQubitGate:
    """Try replacing a given SingleQubitGate with a default SingleQubitGate.
        It does that by matching the input SingleQubitGate to a default SingleQubitGate.

    Returns:
            A default SingleQubitGate if this SingleQubitGate is close to it,
            or the input SingleQubitGate otherwise.
    """
    from opensquirrel.default_instructions import (
        default_bsr_set_without_rn,
        default_bsr_with_angle_param_set,
    )
    from opensquirrel.ir.default_gates.single_qubit_gates import Rn

    for gate_name in default_bsr_set_without_rn:
        arguments: tuple[Any, ...] = (gate.qubit,)
        if gate_name in default_bsr_with_angle_param_set:
            arguments += (Float(gate.bsr.angle),)
        possible_gate = default_bsr_set_without_rn[gate_name](*arguments)
        gate_bsr = BlochSphereRotation(axis=gate.bsr.axis, angle=gate.bsr.angle, phase=gate.bsr.phase)
        if possible_gate.bsr == gate_bsr:
            return possible_gate

    nx, ny, nz = gate.bsr.axis.value
    return Rn(gate.qubit, nx=nx, ny=ny, nz=nz, theta=gate.bsr.angle, phi=gate.bsr.phase)


class SingleQubitGate(Gate):
    bsr: BlochSphereRotation
    matrix: MatrixSemantic

    def __init__(self, qubit: QubitLike, gate_semantic: GateSemantic, name: str = "SingleQubitGate") -> None:
        Gate.__init__(self, name)
        self.qubit = Qubit(qubit)

        self._bsr = gate_semantic if isinstance(gate_semantic, BlochSphereRotation) else None
        self._matrix = gate_semantic if isinstance(gate_semantic, MatrixSemantic) else None

    def __getattr__(self, name: str) -> Any:
        match name:
            case "bsr":
                if self._bsr is None:
                    from opensquirrel.ir.semantics.bsr import bsr_from_matrix

                    self._bsr = bsr_from_matrix(self.matrix)
                return self._bsr
            case "matrix":
                if self._matrix is None:
                    from opensquirrel.utils import can1

                    self._matrix = MatrixSemantic(can1(self.bsr.axis, self.bsr.angle, self.bsr.phase))
                return self._matrix
            case _:
                return self.__getattribute__(name)

    def accept(self, visitor: IRVisitor) -> Any:
        visit_gate = super().accept(visitor)
        return visit_gate if visit_gate is not None else visitor.visit_single_qubit_gate(self)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SingleQubitGate):
            return False

        if self.qubit != other.qubit:
            return False

        return self.bsr == other.bsr

    def __mul__(self, other: SingleQubitGate) -> SingleQubitGate:
        if self.qubit != other.qubit:
            msg = "cannot merge two single qubit gates on different qubits."
            raise ValueError(msg)
        return SingleQubitGate(self.qubit, self.bsr * other.bsr)

    @property
    def arguments(self) -> tuple[Qubit, ...]:
        return (self.qubit,)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]

    def is_identity(self) -> bool:
        if self.bsr is not None:
            return self.bsr.is_identity()
        return self.matrix.is_identity() if self.matrix else False
