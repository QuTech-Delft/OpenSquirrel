import pytest

from opensquirrel.decomposer import XYXDecomposer
from opensquirrel.decomposer.general_decomposer import check_gate_replacement
from opensquirrel.ir import BlochSphereRotation

# Any of the variations of the ABA decomposer has this bug.
DECOMPOSER = XYXDecomposer


@pytest.fixture(name="decomposer")
def decomposer_fixture() -> DECOMPOSER:
    return DECOMPOSER()


def test_specific_bloch_rotation(decomposer: DECOMPOSER) -> None:
    axis = [-0.53825, -0.65289, -0.53294]
    angle = 1.97871
    arbitrary_operation = BlochSphereRotation(qubit=0, axis=axis, angle=angle, phase=0)
    decomposed_arbitrary_operation = decomposer.decompose(arbitrary_operation)
    check_gate_replacement(arbitrary_operation, decomposed_arbitrary_operation)
