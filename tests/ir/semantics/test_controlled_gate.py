from math import pi

import pytest

from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGate


class TestControlledGate:
    def test_control_gate_same_control_and_target_qubit(self) -> None:
        with pytest.raises(ValueError, match="control and target qubit cannot be the same"):
            ControlledGate(0, BlochSphereRotation(0, [0, 0, 1], angle=pi, phase=pi / 2))
