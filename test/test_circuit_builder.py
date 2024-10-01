import re

import pytest

from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.default_gates import CNOT, H, I
from opensquirrel.ir import Bit, Comment, Measure, Qubit


class TestCircuitBuilder:
    def test_simple(self) -> None:
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

    def test_identity(self) -> None:
        builder = CircuitBuilder(1)
        builder.I(Qubit(0))

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 1
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [
            I(Qubit(0)),
        ]

    def test_single_measure(self) -> None:
        builder = CircuitBuilder(1, 1)
        builder.measure(Qubit(0), Bit(0))

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 1
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [
            Measure(Qubit(0), Bit(0)),
        ]

    def test_circuit_measure(self) -> None:
        builder = CircuitBuilder(2, 2)

        builder.H(Qubit(0))
        builder.CNOT(Qubit(0), Qubit(1))
        builder.measure(Qubit(0), Bit(0))
        builder.measure(Qubit(1), Bit(1))

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 2
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [
            H(Qubit(0)),
            CNOT(Qubit(0), Qubit(1)),
            Measure(Qubit(0), Bit(0)),
            Measure(Qubit(1), Bit(1)),
        ]

    def test_chain(self) -> None:
        builder = CircuitBuilder(3)

        circuit = builder.H(Qubit(0)).CNOT(Qubit(0), Qubit(1)).to_circuit()

        assert circuit.ir.statements == [
            H(Qubit(0)),
            CNOT(Qubit(0), Qubit(1)),
        ]

    def test_gate_index_error(self) -> None:
        builder = CircuitBuilder(2)

        with pytest.raises(IndexError) as exception_info:
            builder.H(Qubit(0)).CNOT(Qubit(0), Qubit(12)).to_circuit()
        assert re.search("qubit index is out of bounds", str(exception_info.value))

    def test_measure_index_error(self) -> None:
        builder = CircuitBuilder(2, 1)
        with pytest.raises(IndexError) as exception_info:
            builder.H(Qubit(0)).measure(Qubit(0), Bit(10)).to_circuit()
        assert re.search("bit index is out of bounds", str(exception_info.value))

    def test_unknown_instruction(self) -> None:
        builder = CircuitBuilder(3)
        with pytest.raises(ValueError, match="unknown instruction `unknown`"):
            builder.unknown(0)

    def test_wrong_number_of_arguments(self) -> None:
        builder = CircuitBuilder(3)

        with pytest.raises(TypeError) as exception_info:
            builder.H(Qubit(0), Qubit(1))
        assert re.search(
            r"H\(\) takes 1 positional argument but 2 were given",
            str(exception_info.value),
        )

    def test_wrong_argument_type(self) -> None:
        builder = CircuitBuilder(3)

        with pytest.raises(TypeError) as exception_info:
            builder.H(0)

        assert re.search(
            "wrong argument type for instruction `H`, got <class 'int'> but expected <class 'opensquirrel.ir.Qubit'>",
            str(exception_info.value),
        ) or re.search(
            "wrong argument type for instruction `H`, got <class 'int'> but expected Qubit",
            str(exception_info.value),
        )

    def test_decoupling_circuit_and_builder(self) -> None:
        builder = CircuitBuilder(1)
        circuit = builder.to_circuit()
        assert circuit.ir is not builder.ir
        assert circuit.register_manager is not builder.register_manager
