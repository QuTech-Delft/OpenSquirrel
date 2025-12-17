from math import pi

import pytest

from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate


class TestControlledGate:
    def test_control_gate_same_control_and_target_qubit(self) -> None:
        with pytest.raises(ValueError, match="the qubit from the target gate does not match with 'qubit1'"):
            TwoQubitGate(
                0,
                1,
                gate_semantic=ControlledGateSemantic(
                    SingleQubitGate(0, BlochSphereRotation([0, 0, 1], angle=pi, phase=pi / 2))
                ),
            )
