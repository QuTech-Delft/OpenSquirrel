from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

from opensquirrel.ir import Float, Gate, GateSemantic, Qubit, QubitLike
from opensquirrel.ir.semantics import BlochSphereRotation, MatrixGateSemantic

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
        default_bsr_with_param_set,
        default_single_qubit_gate_set,
    )
    from opensquirrel.ir.default_gates.single_qubit_gates import Rn

    for gate_name in default_single_qubit_gate_set:
        if gate_name in ("Rn", "U"):
            continue

        arguments: tuple[Any, ...] = (gate.qubit,)
        if gate_name in default_bsr_with_param_set:
            arguments += (Float(gate.bsr.angle),)

        possible_gate = default_single_qubit_gate_set[gate_name](*arguments)
        if possible_gate == gate:
            return possible_gate

    nx, ny, nz = gate.bsr.axis.value
    return Rn(gate.qubit, nx=nx, ny=ny, nz=nz, theta=gate.bsr.angle, phi=gate.bsr.phase)


class SingleQubitGate(Gate):
    def __init__(self, qubit: QubitLike, gate_semantic: GateSemantic, name: str = "SingleQubitGate") -> None:
        Gate.__init__(self, name)
        self.qubit = Qubit(qubit)

        self._bsr = gate_semantic if isinstance(gate_semantic, BlochSphereRotation) else None
        self._matrix = gate_semantic if isinstance(gate_semantic, MatrixGateSemantic) else None

    @cached_property
    def bsr(self) -> BlochSphereRotation:
        if self._bsr is None:
            from opensquirrel.ir.semantics.bsr import bsr_from_matrix

            self._bsr = bsr_from_matrix(self.matrix)
        return self._bsr

    @cached_property
    def matrix(self) -> MatrixGateSemantic:
        if self._matrix is None:
            from opensquirrel.utils import can1

            self._matrix = MatrixGateSemantic(can1(self.bsr.axis, self.bsr.angle, self.bsr.phase))
        return self._matrix

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
