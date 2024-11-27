from typing import Callable

import numpy as np
import pytest

from opensquirrel.ir import BlochSphereRotation
from opensquirrel.passes.decomposer import Decomposer, aba_decomposer as aba
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement

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

    arbitrary_operation = BlochSphereRotation(qubit=0, axis=axis, angle=angle, phase=0)
    decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
    check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)


@pytest.mark.parametrize("aba_decomposer", ABA_DECOMPOSER_LIST)
def test_all_octants_of_bloch_sphere_rotation(aba_decomposer: Callable[..., Decomposer]) -> None:
    decomposer = aba_decomposer()
    steps = 6
    coordinates = np.linspace(-1, 1, num=steps)
    angles = np.linspace(-2 * np.pi, 2 * np.pi, num=steps)
    axes = [[i, j, z] for i in coordinates for j in coordinates for z in coordinates]

    for angle in angles:
        for axis in axes:
            arbitrary_operation = BlochSphereRotation(qubit=0, axis=axis, angle=angle, phase=0.1)
            decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
            check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)
