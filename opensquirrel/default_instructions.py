from __future__ import annotations

from collections.abc import Mapping

from opensquirrel.ir import (
    CNOT,
    CR,
    CZ,
    SWAP,
    X90,
    Y90,
    Barrier,
    BlochSphereRotation,
    BsrAngleParam,
    BsrFullParams,
    BsrNoParams,
    ControlledGate,
    CRk,
    Gate,
    H,
    I,
    Init,
    Instruction,
    MatrixGate,
    Measure,
    MinusX90,
    MinusY90,
    NonUnitary,
    Reset,
    Rn,
    Rx,
    Ry,
    Rz,
    S,
    SDagger,
    T,
    TDagger,
    Unitary,
    Wait,
    X,
    Y,
    Z,
)

default_bsr_without_params_set: Mapping[str, type[BsrNoParams]]
default_bsr_without_params_set = {
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
    "mX90": MinusX90,
    "mY90": MinusY90,
}
default_bsr_full_params_set: Mapping[str, type[BsrFullParams]]
default_bsr_full_params_set = {
    "Rn": Rn,
}
default_bsr_with_angle_param_set: Mapping[str, type[BsrAngleParam]]
default_bsr_with_angle_param_set = {
    "Rx": Rx,
    "Ry": Ry,
    "Rz": Rz,
}
default_bloch_sphere_rotation_set: Mapping[str, type[BlochSphereRotation]]
default_bloch_sphere_rotation_set = {
    **default_bsr_full_params_set,
    **default_bsr_without_params_set,
    **default_bsr_with_angle_param_set,
}
default_controlled_gate_set: Mapping[str, type[ControlledGate]]
default_controlled_gate_set = {
    "CNOT": CNOT,
    "CR": CR,
    "CRk": CRk,
    "CZ": CZ,
}
default_matrix_gate_set: Mapping[str, type[MatrixGate]]
default_matrix_gate_set = {
    "SWAP": SWAP,
}
default_gate_alias_set = {
    "Hadamard": H,
    "Identity": I,
}

default_gate_set: Mapping[str, type[Gate]]
default_gate_set = {
    **default_bloch_sphere_rotation_set,
    **default_controlled_gate_set,
    **default_matrix_gate_set,
    **default_gate_alias_set,
}

default_unitary_set: Mapping[str, type[Unitary]]
default_unitary_set = {**default_gate_set}

default_non_unitary_set: Mapping[str, type[NonUnitary]]
default_non_unitary_set = {
    "barrier": Barrier,
    "init": Init,
    "measure": Measure,
    "reset": Reset,
    "wait": Wait,
}

default_instruction_set: Mapping[str, type[Instruction]]
default_instruction_set = {
    **default_unitary_set,
    **default_non_unitary_set,
}


def is_anonymous_gate(name: str) -> bool:
    return name not in default_gate_set
