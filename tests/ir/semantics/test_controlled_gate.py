from math import pi

import pytest

from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGate
from opensquirrel.ir.single_qubit_gate import SingleQubitGate


class TestControlledGate:
    def test_control_gate_same_control_and_target_qubit(self) -> None:
        with pytest.raises(ValueError, match="control and target qubit cannot be the same"):
            ControlledGate(0, SingleQubitGate(0, BlochSphereRotation([0, 0, 1], angle=pi, phase=pi / 2)))
