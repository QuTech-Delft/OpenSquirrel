from math import pi
from typing import cast

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.common import normalize_angle
from opensquirrel.ir import Float

AnglesType = list[tuple[float, float]]


@pytest.fixture
def angles() -> AnglesType:
    delta = 0.1
    f = 3 / 2
    input_angles = [
        pi, -pi, -pi - delta, -pi + delta, f * pi, -f * pi, 2 * pi
    ]
    expected_outputs = [
        pi, pi, pi - delta, -pi + delta, -pi / 2, pi / 2, 0.0
    ]
    return zip(input_angles, expected_outputs)


class TestParsing:

    @staticmethod
    def _check_expected(circuit: Circuit, expected) -> None:
        for statement in circuit.ir.statements:
            assert getattr(statement, "theta").value == expected
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
            theta_expected = cast(Float, builder.ir.statements[i].arguments[-1])
            assert theta_expected.value == normalize_angle(2 * pi / 2**k)

        # with pytest.raises(
        #     TypeError,
        #     match=r"trying to build 'CRk' with the wrong number or type of arguments: '\(0, 1, 1.5\)': "
        #           r"parameter 'k' should be of type 'int', but got '<class 'float'>' instead"
        # ):
        #     builder.CRk(0, 1, 1.5)

    # @pytest.mark.parametrize(
    #     ("cq_string", "expected_instruction"),
    #     [
    #         # ("version 3; qubit q; inv.X q", [Rn(0, 1.0, 0.0, 0.0, 3.1415927, -1.5707963)]),
    #         ("version 3; qubit q; pow(1.0/2).Rn(1.0, 0.0, 0.0, 2 * pi, pi) q", [Rx(0, pi)]),
    #         # ("version 3; qubit q; pow(2).X q", []),
    #         # ("version 3; qubit q; pow(4).X q", []),
    #         # ("version 3; qubit[2] q; ctrl.Rx(-pi) q[0], q[1]", []),
    #     ],
    #     # ids=["inv", "pow-1/2", "pow-2", "pow-4", "ctrl"]
    # )
    # def test_gate_modifiers(self, cq_string: str, expected_instruction: list) -> None:
    #     circuit = Circuit.from_string(cq_string)


