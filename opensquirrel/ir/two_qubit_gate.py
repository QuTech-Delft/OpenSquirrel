from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any

import numpy as np

from opensquirrel.ir import Float, Gate, IRVisitor, Qubit, QubitLike
from opensquirrel.ir.semantics import CanonicalGateSemantic, ControlledGateSemantic, MatrixGateSemantic
from opensquirrel.ir.semantics.bsr import bsr_from_matrix

if TYPE_CHECKING:
    from opensquirrel.ir.semantics.gate_semantic import GateSemantic


def try_match_replace_with_default_two_qubit_gate(gate: TwoQubitGate) -> TwoQubitGate:
    """Tries to match a given two-qubit gate with a _default_ two-qubit gate.
    It does that by checking if the parameters of the Bloch sphere rotation (BSR) semantic of the
    input two-qubit gate are close to those of any of the default two-qubit gates.

    Note:
        - The default (two-qubit) gates are defined in the
        [cQASM standard gate set](https://qutech-delft.github.io/cQASM-spec/latest/standard_gate_set/index.html).
        - If no specific match is found, the general Rn gate is returned with the same parameters
        values as those of the input gate.

    Args:
        gate: The two-qubit gate to be matched.

    Returns:
        A default two-qubit gate if this two-qubit gate matches it, otherwise return the input gate.

    """
    from opensquirrel.default_instructions import (
        default_two_qubit_gate_set,
        default_two_qubit_gate_with_param_set,
    )

    if gate.name in default_two_qubit_gate_set:
        return gate

    for gate_name in default_two_qubit_gate_set:
        arguments: tuple[Any, ...] = (gate.qubit0, gate.qubit1)
        if gate_name in default_two_qubit_gate_with_param_set and gate.controlled:
            arguments += (Float(gate.controlled.target_bsr.angle),)

        try:
            possible_gate = default_two_qubit_gate_set[gate_name](*arguments)  # ty: ignore[invalid-argument-type]
        except (TypeError, ValueError):
            continue

        if possible_gate == gate:
            return possible_gate

    return gate


class TwoQubitGate(Gate):
    def __init__(
        self, qubit0: QubitLike, qubit1: QubitLike, gate_semantic: GateSemantic, name: str = "TwoQubitGate"
    ) -> None:
        Gate.__init__(self, name)
        self.qubit0 = Qubit(qubit0)
        self.qubit1 = Qubit(qubit1)

        self._controlled = gate_semantic if isinstance(gate_semantic, ControlledGateSemantic) else None
        self._matrix = gate_semantic if isinstance(gate_semantic, MatrixGateSemantic) else None
        self._canonical = gate_semantic if isinstance(gate_semantic, CanonicalGateSemantic) else None
        self.gate_semantic = gate_semantic

        if self._check_repeated_qubit_operands(self.qubit_operands):
            msg = "qubit operands cannot be the same qubit"
            raise ValueError(msg)

    @cached_property
    def matrix(self) -> MatrixGateSemantic:
        if self._matrix:
            return self._matrix

        if self._controlled:
            from opensquirrel.utils.matrix_expander import can1

            target_bsr = self._controlled.target_bsr
            u_target = can1(target_bsr.axis, target_bsr.angle, target_bsr.phase)
            m = np.eye(4, dtype=np.complex128)
            m[2:, 2:] = u_target
            self._matrix = MatrixGateSemantic(m)
            return self._matrix

        if self._canonical:
            from opensquirrel.utils.matrix_expander import can1, can2

            if self._canonical.rotations:
                k1, k2, k3, k4 = (
                    can1(rotation.axis, rotation.angle, rotation.phase) for rotation in self._canonical.rotations
                )
                return MatrixGateSemantic(np.kron(k3, k4) @ can2(self._canonical.axis) @ np.kron(k1, k2))
            return MatrixGateSemantic(can2(self._canonical.axis))

        msg = f"invalid gate semantic: {self.gate_semantic}"
        raise ValueError(msg)

    @cached_property
    def canonical(self) -> CanonicalGateSemantic:
        if not self._canonical:
            from opensquirrel.utils.matrix_expander import canonical_decomposition

            k1, k2, k3, k4, axis = canonical_decomposition(np.array(self.matrix))

            bsr1 = bsr_from_matrix(k1)
            bsr2 = bsr_from_matrix(k2)
            bsr3 = bsr_from_matrix(k3)
            bsr4 = bsr_from_matrix(k4)
            self._canonical = CanonicalGateSemantic(axis, [bsr1, bsr2, bsr3, bsr4])
        return self._canonical

    @cached_property
    def controlled(self) -> ControlledGateSemantic | None:
        return self._controlled

    @property
    def qubit_operands(self) -> tuple[Qubit, ...]:
        return (self.qubit0, self.qubit1)

    def accept(self, visitor: IRVisitor) -> Any:
        """Accepts visitor and processes this IR node."""
        visit_parent = super().accept(visitor)
        return visit_parent if visit_parent is not None else visitor.visit_two_qubit_gate(self)

    def is_identity(self) -> bool:
        """Checks if the two-qubit gate is an identity gate.

        Returns:
            True if the two-qubit gate is an identity gate, False otherwise.

        """
        if self.controlled:
            return self.controlled.is_identity()
        if self.matrix:
            return self.matrix.is_identity()
        if self.canonical:
            return self.canonical.is_identity()
        return False

    def __repr__(self) -> str:
        return f"TwoQubitGate(qubits=[{self.qubit0, self.qubit1}], gate_semantic={self.gate_semantic})"
