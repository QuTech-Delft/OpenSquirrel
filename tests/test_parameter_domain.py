from collections.abc import Iterator
from math import pi
from typing import cast

import pytest

from opensquirrel import Circuit, CircuitBuilder, Rn, Rx, Ry, Rz, X
from opensquirrel.common import normalize_angle
from opensquirrel.ir import Float, Gate, Instruction
from opensquirrel.ir.semantics import ControlledGate
from opensquirrel.passes.merger import SingleQubitGatesMerger

AnglesType = Iterator[tuple[float, float]]

DELTA = 0.001


@pytest.fixture
def angles() -> AnglesType:
    input_angles = [pi, -pi, -pi - DELTA, -pi + DELTA, 3 * pi / 2, -3 * pi / 2, 2 * pi]
    expected_outputs = [pi, pi, pi - DELTA, -pi + DELTA, -pi / 2, pi / 2, 0.0]
    return zip(input_angles, expected_outputs)


class TestParsing:
    @staticmethod
    def _check_expected(circuit: Circuit, expected: float) -> None:
        for statement in circuit.ir.statements:
            assert getattr(statement, "theta").value == expected  # noqa
            phi = getattr(statement, "phi", None)
            assert phi.value == expected if phi else True

    def test_circuit_from_string(self, angles: AnglesType) -> None:
        for angle, expected in angles:
            circuit = Circuit.from_string(
                f"version 3; qubit[2] q; Rx({angle}) q[0]; Rn(1,1,1,{angle},{angle}) q[0]; CR({angle}) q[0], q[1]"
            )
            TestParsing._check_expected(circuit, expected)

        with pytest.raises(
            OSError,
            match=r"parsing error: Error at <unknown file name>:1:26..29: failed to resolve 'CRk' with parameter type"
            r" \(float\)",
        ):
            Circuit.from_string("version 3.0; qubit[2] q; CRk(1.5) q[0], q[1]")

    def test_circuit_builder(self, angles: AnglesType) -> None:
        for angle, expected in angles:
            builder = CircuitBuilder(2)
            builder.Rx(0, angle).Rn(0, 1, 1, 1, angle, angle).CR(0, 1, angle)
            circuit = builder.to_circuit()
            TestParsing._check_expected(circuit, expected)

        builder = CircuitBuilder(2)
        for i, k in enumerate([0, 1, -1, 2, 4]):
            builder.CRk(0, 1, k)
            theta_expected = cast("Float", cast("Instruction", builder.ir.statements[i]).arguments[-1])
            assert theta_expected.value == normalize_angle(2 * pi / 2**k)

        with pytest.warns(UserWarning, match=r"value of parameter 'k' is not an integer: got <class 'float'> instead."):
            builder.CRk(0, 1, 1.5)

    @pytest.mark.parametrize(
        ("cq_string", "expected"),
        [
            ("version 3; qubit q; inv.X q", [Rn(0, 1.0, 0.0, 0.0, pi, -1.5707963)]),
            ("version 3; qubit q; pow(1.0/2).Rn(1.0, 0.0, 0.0, 2 * pi, pi) q", [X(0)]),
            ("version 3; qubit q; pow(2).X q", [Rn(0, 1.0, 0.0, 0.0, 0.0, pi)]),
            ("version 3; qubit q; pow(4).X q", [Rx(0, 0.0)]),
            ("version 3; qubit[2] q; ctrl.Rx(-pi) q[0], q[1]", [ControlledGate(0, Rx(1, pi))]),
        ],
        ids=["inv", "pow-1/2", "pow-2", "pow-4", "ctrl"],
    )
    def test_gate_modifiers(self, cq_string: str, expected: list[Gate]) -> None:
        circuit = Circuit.from_string(cq_string)
        assert circuit.ir.statements == expected


class TestMerging:
    def test_merge_rotation_gates(self) -> None:
        circuit = CircuitBuilder(1).Rx(0, -pi).Rn(0, 1, 0, 0, 0, pi / 2).to_circuit()
        circuit.merge(merger=SingleQubitGatesMerger())
        assert circuit.ir.statements[0] == X(0)

        circuit = CircuitBuilder(1).Ry(0, -pi).Ry(0, -DELTA).to_circuit()
        circuit.merge(merger=SingleQubitGatesMerger())
        assert circuit.ir.statements[0] == Ry(0, pi - DELTA)

        circuit = CircuitBuilder(1).Rz(0, pi).Rz(0, pi / 2).to_circuit()
        circuit.merge(merger=SingleQubitGatesMerger())
        assert circuit.ir.statements[0] == Rz(0, -pi / 2)
