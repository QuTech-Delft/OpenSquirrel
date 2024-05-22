import re

import pytest

from open_squirrel.circuit_builder import CircuitBuilder
from open_squirrel.default_gates import CNOT, H, I
from open_squirrel.ir import Comment, Measure, Qubit


class TestCircuitBuilder:
    def test_simple(self):
        builder = CircuitBuilder(2)

        builder.comment("A single line comment.")
        builder.H(Qubit(0))
        builder.CNOT(Qubit(0), Qubit(1))

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 2
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [
            Comment("A single line comment."),
            H(Qubit(0)),
            CNOT(Qubit(0), Qubit(1)),
        ]

    def test_identity(self):
        builder = CircuitBuilder(1)
        builder.I(Qubit(0))

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 1
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [
            I(Qubit(0)),
        ]

    def test_single_measure(self):
        builder = CircuitBuilder(1)
        builder.measure(Qubit(0))

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 1
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [
            Measure(Qubit(0)),
        ]

    def test_circuit_measure(self):
        builder = CircuitBuilder(2)

        builder.H(Qubit(0))
        builder.CNOT(Qubit(0), Qubit(1))
        builder.measure(Qubit(0))
        builder.measure(Qubit(1))

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 2
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [
            H(Qubit(0)),
            CNOT(Qubit(0), Qubit(1)),
            Measure(Qubit(0)),
            Measure(Qubit(1)),
        ]

    def test_chain(self):
        builder = CircuitBuilder(3)

        circuit = builder.H(Qubit(0)).CNOT(Qubit(0), Qubit(1)).to_circuit()

        assert circuit.ir.statements == [
            H(Qubit(0)),
            CNOT(Qubit(0), Qubit(1)),
        ]

    def test_unknown_instruction(self):
        builder = CircuitBuilder(3)

        with pytest.raises(Exception) as exception_info:
            builder.unknown(0)
        assert re.search("Unknown instruction `unknown`", str(exception_info.value))

    def test_wrong_number_of_arguments(self):
        builder = CircuitBuilder(3)

        with pytest.raises(Exception) as exception_info:
            builder.H(Qubit(0), Qubit(1))
        assert re.search(r"H\(\) takes 1 positional argument but 2 were given", str(exception_info.value))

    def test_wrong_argument_type(self):
        builder = CircuitBuilder(3)

        with pytest.raises(Exception) as exception_info:
            builder.H(0)
        assert re.search(
            "Wrong argument type for instruction `H`, got <class 'int'> but expected <class "
            "'open_squirrel.ir.Qubit'>",
            str(exception_info.value),
        )
