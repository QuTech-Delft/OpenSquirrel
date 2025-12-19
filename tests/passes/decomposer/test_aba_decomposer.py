import itertools
from collections.abc import Callable

import numpy as np
import pytest

from opensquirrel import U
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.passes.decomposer import aba_decomposer as aba
from opensquirrel.passes.decomposer.general_decomposer import Decomposer, check_gate_replacement

ABA_DECOMPOSER_LIST = [
    aba.XYXDecomposer,
    aba.XZXDecomposer,
    aba.YXYDecomposer,
    aba.YZYDecomposer,
    aba.ZXZDecomposer,
    aba.ZYZDecomposer,
]


@pytest.mark.parametrize("aba_decomposer", ABA_DECOMPOSER_LIST)
def test_specific_bloch_rotation(aba_decomposer: Callable[..., Decomposer]) -> None:
    decomposer = aba_decomposer()
    axis = [-0.53825, -0.65289, -0.53294]
    angle = 1.97871

    arbitrary_operation = SingleQubitGate(qubit=0, gate_semantic=BlochSphereRotation(axis=axis, angle=angle, phase=0))

    decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
    check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)

    u_gate = U(0, 1, 2, 3)
    decomposed_u_gate = decomposer.decompose(u_gate)
    check_gate_replacement(u_gate, decomposed_u_gate)


@pytest.mark.parametrize("aba_decomposer", ABA_DECOMPOSER_LIST)
def test_all_octants_of_bloch_sphere_rotation(aba_decomposer: Callable[..., Decomposer]) -> None:
    decomposer = aba_decomposer()
    steps = 5
    phase_steps = 3
    coordinates = np.linspace(-1, 1, num=steps)
    angles = np.linspace(-2 * np.pi, 2 * np.pi, num=steps)
    phases = np.linspace(-np.pi, np.pi, num=phase_steps)
    axes = [[x, y, z] for x, y, z in list(itertools.permutations(coordinates, 3)) if [x, y, z] != [0, 0, 0]]

    for axis in axes:
        for angle in angles:
            for phase in phases:
                arbitrary_operation = SingleQubitGate(
                    qubit=0, gate_semantic=BlochSphereRotation(axis=axis, angle=angle, phase=phase)
                )
                decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
                check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)
