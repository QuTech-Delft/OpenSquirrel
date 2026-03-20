from math import pi, sqrt

import pytest

from opensquirrel import Ry, Rz
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.ir import Axis, Gate, Measure
from opensquirrel.passes.decomposer.measure_decomposer import MeasureDecomposer


class TestMeasureDecomposer:
    @pytest.mark.parametrize(
        ("axis", "gates"),
        [
            (Axis(1 / sqrt(2), 0, 1 / sqrt(2)), [Ry(0, -pi / 4)]),
            (Axis(1, 0, 0), [Ry(0, -pi / 2)]),
            (Axis(0, 1, 0), [Rz(0, -pi / 2), Ry(0, -pi / 2)]),
            (Axis(0, 0, 1), []),
            (Axis(0.5, 0.25, 0.33), [Rz(0, -0.463647609), Ry(0, -1.0375234)]),
        ],
        ids=["H", "X", "Y", "Z", "arbitrary"],
    )
    def test_decompose_measure(self, axis: Axis, gates: list[Gate]) -> None:

        builder = CircuitBuilder(1, 1)
        builder.measure(0, 0, axis)
        circuit = builder.to_circuit()

        circuit.decompose(MeasureDecomposer())

        statements = circuit.ir.statements

        gate_statements = [gate for gate in statements if isinstance(gate, Gate)]
        measure_statement = statements[-1]
        assert gate_statements == gates
        assert isinstance(measure_statement, Measure)
