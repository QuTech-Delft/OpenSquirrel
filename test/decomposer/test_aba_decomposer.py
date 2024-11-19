from typing import Callable

import pytest

from opensquirrel.decomposer import (
    Decomposer,
    XYXDecomposer,
    XZXDecomposer,
    YXYDecomposer,
    YZYDecomposer,
    ZXZDecomposer,
    ZYZDecomposer,
)
from opensquirrel.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.ir import BlochSphereRotation

DECOMPOSER = [XYXDecomposer, XZXDecomposer, YXYDecomposer, YZYDecomposer, ZXZDecomposer, ZYZDecomposer]


@pytest.mark.parametrize("decomposer_class", DECOMPOSER)
def test_specific_bloch_rotation(decomposer_class: Callable[..., Decomposer]) -> None:
    decomposer = decomposer_class()
    axis = [-0.53825, -0.65289, -0.53294]
    angle = 1.97871

    arbitrary_operation = BlochSphereRotation(qubit=0, axis=axis, angle=angle, phase=0)
    decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
    check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)


@pytest.mark.parametrize("decomposer_class", DECOMPOSER)
def test_negative_bloch_rotation(decomposer_class: Callable[..., Decomposer]) -> None:
    decomposer = decomposer_class()
    axis = [-0.5789, -0.9000, -3.53294]
    angle = 3.12
    arbitrary_operation = BlochSphereRotation(qubit=0, axis=axis, angle=angle, phase=0)
    decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
    check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)
