import numpy as np
import pytest

from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.default_gates import CNOT, H, I
from opensquirrel.ir import Bit, Comment, Float, Measure


class TestCircuitBuilder:
    def test_simple(self) -> None:
        builder = CircuitBuilder(2)

        builder.comment("A single line comment.")
        builder.H(0)
        builder.CNOT(0, 1)

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 2
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [
            Comment("A single line comment."),
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
        builder.measure(0, Bit(0))

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 1
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [Measure(0, Bit(0))]

    def test_circuit_measure(self) -> None:
        builder = CircuitBuilder(2, 2)

        builder.H(0)
        builder.CNOT(0, 1)
        builder.measure(0, Bit(0))
        builder.measure(1, Bit(1))

        circuit = builder.to_circuit()

        assert circuit.qubit_register_size == 2
        assert circuit.qubit_register_name == "q"
        assert circuit.ir.statements == [
            H(0),
            CNOT(0, 1),
            Measure(0, Bit(0)),
            Measure(1, Bit(1)),
        ]

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
            builder.H(0).measure(0, Bit(10)).to_circuit()

    def test_unknown_instruction(self) -> None:
        builder = CircuitBuilder(3)
        with pytest.raises(ValueError, match="unknown instruction `unknown`"):
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

    def test_initial_barrier(self) -> None:
        builder = CircuitBuilder(2)
        circuit = builder.H(0).barrier(0).H(1).barrier(1).H(0).Rx(0, Float(np.pi / 3)).barrier(0).to_circuit()
        circuit.merge_single_qubit_gates()
        print(circuit)
        assert (
            str(circuit)
            == """version 3.0

qubit[2] q

H q[0]
H q[1]
barrier q[0]
Anonymous gate: BlochSphereRotation(Qubit[0], axis=[ 0.65465 -0.37796  0.65465], angle=-2.41886, phase=1.5708)
barrier q[1]
barrier q[0]
"""
        )

    def test_barrier_with_CNOT(self) -> None:
        builder = CircuitBuilder(2)
        circuit = builder.X(0).barrier(0).X(1).barrier(1).CNOT(0, 1).barrier(1).X(1).to_circuit()
        circuit.merge_single_qubit_gates()
        assert (
            str(circuit)
            == """version 3.0

qubit[2] q

X q[0]
X q[1]
barrier q[0]
barrier q[1]
CNOT q[0], q[1]
barrier q[1]
X q[1]
"""
        )

    def test_barrier_unpacking_use_case(self) -> None:
        builder = CircuitBuilder(2)
        circuit = builder.X(0).X(1).barrier(0).barrier(1).X(0).to_circuit()
        circuit.merge_single_qubit_gates()
        assert (
            str(circuit)
            == """version 3.0

qubit[2] q

X q[0]
X q[1]
barrier q[0]
barrier q[1]
X q[0]
"""
        )

    def test_barrier_4_qubit(self) -> None:
        builder = CircuitBuilder(4)
        circuit = (
            builder
            .H(0)
            .barrier(0)
            .H(1)
            .barrier(1)
            .H(2)
            .barrier(2)
            .H(3)
            .barrier(3)
            .CNOT(0, 3)
            .barrier(0)
            .barrier(1)
            .barrier(3)
            .to_circuit()
        )
        circuit.merge_single_qubit_gates()
        assert (
            str(circuit)
            == """version 3.0

qubit[4] q

H q[0]
H q[1]
H q[2]
H q[3]
barrier q[0]
barrier q[1]
barrier q[2]
barrier q[3]
CNOT q[0], q[3]
barrier q[0]
barrier q[1]
barrier q[3]
"""
        )

    def test_only_barriers(self) -> None:
        builder = CircuitBuilder(4)
        circuit = (
            builder.barrier(0).barrier(1).barrier(2).barrier(3).CNOT(0, 3).barrier(0).barrier(1).barrier(3).to_circuit()
        )
        circuit.merge_single_qubit_gates()
        assert (
            str(circuit)
            == """version 3.0

qubit[4] q

barrier q[0]
barrier q[1]
barrier q[2]
barrier q[3]
CNOT q[0], q[3]
barrier q[0]
barrier q[1]
barrier q[3]
"""
        )
