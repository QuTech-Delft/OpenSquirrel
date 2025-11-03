from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import numpy as np

from opensquirrel.circuit import Circuit
from opensquirrel.common import ATOL
from opensquirrel.exceptions import ExporterError, UnsupportedGateError
from opensquirrel.ir import Gate, IRVisitor, Measure, Reset
from opensquirrel.ir.semantics import (
    BlochSphereRotation,
    BsrAngleParam,
    BsrFullParams,
    BsrNoParams,
    ControlledGate,
    MatrixGate,
)

try:
    import qiskit
    import qiskit.circuit.library
except ModuleNotFoundError:
    pass

if TYPE_CHECKING:
    from opensquirrel import (
        CNOT,
        CR,
        SWAP,
        CRk,
    )
    from opensquirrel.circuit import Circuit
    from opensquirrel.ir import Qubit
    from opensquirrel.register_manager import RegisterManager

# Radian to degree conversion outcome precision
FIXED_POINT_DEG_PRECISION = 6

_pauli_i = np.eye(2, dtype=complex)
_pauli_x = np.array([[0, 1], [1, 0]], dtype=complex)
_pauli_y = np.array([[0, -1j], [1j, 0]], dtype=complex)
_pauli_z = np.array([[1, 0], [0, -1]], dtype=complex)


def bsr_to_unitary(gate: Gate) -> np.ndarray:
    k = np.asarray(gate.axis)
    theta = gate.angle

    # from Nielsen and Chuang
    return math.cos(theta / 2) * _pauli_i - 1j * np.sin(theta / 2) * (
        k[0] * _pauli_x + k[1] * _pauli_y + k[2] * _pauli_z
    )


class _QiskitCreator(IRVisitor):
    def _get_qubit_string(self, qubit: Qubit) -> str:
        return f"{self.qubit_register_name}[{qubit.index}]"

    def __init__(self, register_manager: RegisterManager) -> None:
        self.register_manager = register_manager
        self.qubit_register_size = register_manager.get_qubit_register_size()
        self.qubit_register_name = register_manager.get_qubit_register_name()
        self.bit_register_size = register_manager.get_bit_register_size()
        self.acq_index_record = [0] * self.qubit_register_size
        self.bit_string_mapping: list[tuple[None, None] | tuple[int, int]] = [(None, None)] * self.bit_register_size
        self.qiskit_circuit = qiskit.circuit.QuantumCircuit(
            self.qubit_register_size, self.bit_register_size, name="Exported OpenSquirrel circuit"
        )

    def visit_bloch_sphere_rotation(self, gate: BlochSphereRotation) -> None:
        # print(f'_QiskitCreator: visit_bloch_sphere_rotation: {id(gate)}')

        _QiskitCreator.gate = gate

        if abs(gate.axis[0]) < ATOL and abs(gate.axis[1]) < ATOL:
            # Rz rotation.
            theta = round(math.degrees(gate.angle), FIXED_POINT_DEG_PRECISION)
            self.qiskit_circuit.rz(theta, gate.qubit.index)

            return

        u = bsr_to_unitary(gate)
        return self.qiskit_circuit.unitary(u, gate.qubit.index)

    def visit_gate(self, gate: Gate) -> Any:
        if gate.name == "H":
            return self.visit_h(gate)
        return None

    def visit_bsr_no_params(self, gate: BsrNoParams) -> None:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_bsr_full_params(self, gate: BsrFullParams) -> None:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> None:
        return self.visit_bloch_sphere_rotation(gate)

    def visit_matrix_gate(self, gate: MatrixGate) -> None:
        raise UnsupportedGateError(gate)

    def visit_swap(self, gate: SWAP) -> None:
        return self.qiskit_circuit.swap(gate.control_qubit.index, gate.target_qubit.index)

    def visit_controlled_gate(self, gate: ControlledGate) -> None:
        if not isinstance(gate.target_gate, BlochSphereRotation):
            raise UnsupportedGateError(gate)

    def visit_cz(self, gate: CZ) -> None:
        return self.qiskit_circuit.cz(gate.control_qubit.index, gate.target_qubit.index)

    def visit_cnot(self, gate: CNOT) -> None:
        return self.qiskit_circuit.cx(gate.control_qubit.index, gate.target_qubit.index)

    def visit_h(self, gate: H) -> None:
        return self.qiskit_circuit.h(gate.qubit.index)

    def visit_cr(self, gate: CR) -> None:
        raise UnsupportedGateError(gate)

    def visit_crk(self, gate: CRk) -> None:
        raise UnsupportedGateError(gate)

    def visit_measure(self, gate: Measure) -> None:
        qubit_index = gate.qubit.index
        bit_index = gate.bit.index

        self.qiskit_circuit.measure(qubit_index, bit_index)
        return

    def visit_reset(self, gate: Reset) -> Any:
        raise UnsupportedGateError(gate)


# %%
def export(circuit: Circuit) -> tuple[qiskit.circuit.QuantumCircuit, list[tuple[Any, Any]]]:
    if "qiskit" not in globals():

        class QiskitNotInstalled:
            def __getattr__(self, attr_name: Any) -> None:
                msg = "qiskit is not installed, or cannot be installed on your system"
                raise ModuleNotFoundError(msg)

        global qiskit
        qiskit = QiskitNotInstalled()

    qiskit_creator = _QiskitCreator(circuit.register_manager)
    try:
        circuit.ir.accept(qiskit_creator)
    except UnsupportedGateError as e:
        msg = (
            f"cannot export circuit: {e}. "
            "Decompose all gates to the Quantify-scheduler gate set first (rxy, rz, cnot, cz)"
        )
        raise ExporterError(msg) from e
    return qiskit_creator.qiskit_circuit, qiskit_creator.bit_string_mapping


if __name__ == "__main__":
    from rich import print as rprint
    from importlib import reload
    import opensquirrel.ir

    reload(opensquirrel.ir)
    reload(opensquirrel.ir.semantics.bsr)
    reload(opensquirrel.ir)
    import opensquirrel.circuit_builder

    reload(opensquirrel.circuit_builder)
    from opensquirrel.circuit_builder import *

    from opensquirrel import CircuitBuilder

    builder = CircuitBuilder(qubit_register_size=3, bit_register_size=2)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.Rz(0.2, 0)
    builder.CZ(2, 0)
    builder.CNOT(0, 2)
    builder.measure(1, 0)
    builder.S(1)
    qc = builder.to_circuit()
    rprint(qc.ir)

    circuit, _ = export(qc)

    if 1:
        rprint()
        rprint(circuit.decompose().draw())

        w = circuit.decompose()
        rprint()
        rprint(w.draw())

        w = qiskit.transpile(w, basis_gates=["cx", "cz", "rx", "rz"])
        rprint()
        rprint(w.draw())
