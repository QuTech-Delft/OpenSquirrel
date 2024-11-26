import pytest

from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.default_instructions import CNOT, H, I
from opensquirrel.ir import Measure


class TestCircuitBuilder:
    def test_simple(self) -> None:
        builder = CircuitBuilder(2)

        builder.H(0)
        builder.CNOT(0, 1)

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 2
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [
            H(0),
            CNOT(0, 1),
        ]

    def test_identity(self) -> None:
        builder = CircuitBuilder(1)
        builder.I(0)

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 1
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [I(0)]

    def test_single_measure(self) -> None:
        builder = CircuitBuilder(1, 1)
        builder.measure(0, 0)

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 1
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [Measure(0, 0)]

    def test_circuit_measure(self) -> None:
        builder = CircuitBuilder(2, 2)

        builder.H(0)
        builder.CNOT(0, 1)
        builder.measure(0, 0)
        builder.measure(1, 1)

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 2
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [H(0), CNOT(0, 1), Measure(0, 0), Measure(1, 1)]

    def test_chain(self) -> None:
        builder = CircuitBuilder(3)

        circuit = builder.H(0).CNOT(0, 1).to_circuit()

        assert circuit.ir.statements == [H(0), CNOT(0, 1)]

    def test_gate_index_error(self) -> None:
        builder = CircuitBuilder(2)

        with pytest.raises(IndexError, match="qubit index is out of bounds"):
            builder.H(0).CNOT(0, 12).to_circuit()

    def test_measure_index_error(self) -> None:
        builder = CircuitBuilder(2, 1)
        with pytest.raises(IndexError, match="bit index is out of bounds"):
            builder.H(0).measure(0, 10).to_circuit()

    def test_unknown_instruction(self) -> None:
        builder = CircuitBuilder(3)
        with pytest.raises(ValueError, match="unknown instruction 'unknown'"):
            builder.unknown(0)

    def test_wrong_number_of_arguments(self) -> None:
        builder = CircuitBuilder(3)

        with pytest.raises(TypeError, match=".* takes 1 positional argument but 2 were given"):
            builder.H(0, 1)

    def test_decoupling_circuit_and_builder(self) -> None:
        builder = CircuitBuilder(1)
        circuit = builder.to_circuit()
        assert circuit.ir is not builder.ir
        assert circuit.register_manager is not builder.register_manager

    def test_int_qubit_parsing(self) -> None:
        builder = CircuitBuilder(3)

        circuit = builder.H(0).CNOT(0, 1).to_circuit()

        assert circuit.ir.statements == [H(0), CNOT(0, 1)]
