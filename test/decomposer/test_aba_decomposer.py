from typing import Callable

import numpy as np
import pytest

from opensquirrel.ir import BlochSphereRotation
from opensquirrel.passes.decomposer import Decomposer, aba_decomposer as aba
from opensquirrel.passes.decomposer.general_decomposer import check_gate_replacement

DECOMPOSER = [
    aba.XYXDecomposer,
    aba.XZXDecomposer,
    aba.YXYDecomposer,
    aba.YZYDecomposer,
    aba.ZXZDecomposer,
    aba.ZYZDecomposer,
]


@pytest.mark.parametrize("decomposer_class", DECOMPOSER)
def test_specific_bloch_rotation(decomposer_class: Callable[..., Decomposer]) -> None:
    decomposer = decomposer_class()
    axis = [-0.53825, -0.65289, -0.53294]
    angle = 1.97871

    arbitrary_operation = BlochSphereRotation(qubit=0, axis=axis, angle=angle, phase=0)
    decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
    check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)


@pytest.mark.parametrize("decomposer_class", DECOMPOSER)
def test_full_sphere(decomposer_class: Callable[..., Decomposer]) -> None:
    decomposer = decomposer_class()
    steps = 6
    coordinates = np.linspace(-1, 1, num=steps)
    angles = np.linspace(-2 * np.pi, 2 * np.pi, num=steps)
    axis_list = [[i, j, z] for i in coordinates for j in coordinates for z in coordinates]

    for angle in angles:
        for axis in axis_list:
            arbitrary_operation = BlochSphereRotation(qubit=0, axis=axis, angle=angle, phase=0.1)
            decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
            check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)
