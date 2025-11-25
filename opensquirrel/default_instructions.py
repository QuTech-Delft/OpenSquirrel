from __future__ import annotations

from typing import TYPE_CHECKING

from opensquirrel.ir import (
    Barrier,
    Init,
    Measure,
    Reset,
    Wait,
)
from opensquirrel.ir.default_gates import (
    CNOT,
    CR,
    CZ,
    SWAP,
    X90,
    Y90,
    Z90,
    CRk,
    H,
    I,
    MinusX90,
    MinusY90,
    MinusZ90,
    Rn,
    Rx,
    Ry,
    Rz,
    S,
    SDagger,
    T,
    TDagger,
    U,
    X,
    Y,
    Z,
)

if TYPE_CHECKING:
    from opensquirrel.ir import ControlInstruction, Gate, Instruction, NonUnitary, Unitary
    from opensquirrel.ir.semantics import (
        ControlledGate,
        MatrixGate,
    )
    from opensquirrel.ir.single_qubit_gate import SingleQubitGate

default_bsr_without_params_set: dict[str, type[SingleQubitGate]] = {
    "H": H,
    "I": I,
    "S": S,
    "Sdag": SDagger,
    "T": T,
    "Tdag": TDagger,
    "X": X,
    "X90": X90,
    "Y": Y,
    "Y90": Y90,
    "Z": Z,
    "Z90": Z90,
    "mX90": MinusX90,
    "mY90": MinusY90,
    "mZ90": MinusZ90,
}

default_bsr_full_params_set: dict[str, type[SingleQubitGate]] = {
    "Rn": Rn,
}

default_bsr_with_angle_param_set: dict[str, type[SingleQubitGate]] = {
    "Rx": Rx,
    "Ry": Ry,
    "Rz": Rz,
}

default_bsr_unitary_param_set: dict[str, type[SingleQubitGate]] = {
    "U": U,
}
default_bloch_sphere_rotation_set: dict[str, type[SingleQubitGate]] = {
    **default_bsr_full_params_set,
    **default_bsr_without_params_set,
    **default_bsr_with_angle_param_set,
    **default_bsr_unitary_param_set,
}
default_controlled_gate_set: dict[str, type[ControlledGate]] = {
    "CNOT": CNOT,
    "CR": CR,
    "CRk": CRk,
    "CZ": CZ,
}
default_matrix_gate_set: dict[str, type[MatrixGate]] = {
    "SWAP": SWAP,
}
default_gate_alias_set = {
    "Hadamard": H,
    "Identity": I,
}
default_gate_set: dict[str, type[Gate]] = {
    **default_bloch_sphere_rotation_set,
    **default_controlled_gate_set,
    **default_matrix_gate_set,
    **default_gate_alias_set,
}
default_unitary_set: dict[str, type[Unitary]] = {**default_gate_set}
default_non_unitary_set: dict[str, type[NonUnitary]] = {
    "init": Init,
    "measure": Measure,
    "reset": Reset,
}
default_control_instruction_set: dict[str, type[ControlInstruction]] = {
    "barrier": Barrier,
    "wait": Wait,
}
default_instruction_set: dict[str, type[Instruction]] = {
    **default_unitary_set,
    **default_non_unitary_set,
    **default_control_instruction_set,
}

default_bsr_set_without_rn: dict[str, type[SingleQubitGate]]
default_bsr_set_without_rn = {**default_bsr_without_params_set, **default_bsr_with_angle_param_set}


def is_anonymous_gate(name: str) -> bool:
    return name not in default_gate_set
