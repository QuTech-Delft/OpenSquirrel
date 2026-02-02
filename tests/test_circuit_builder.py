import math

import pytest

from opensquirrel import (
    CNOT,
    CZ,
    SWAP,
    X90,
    Y90,
    Z90,
    Barrier,
    BitRegister,
    CircuitBuilder,
    H,
    I,
    Init,
    Measure,
    MinusX90,
    MinusY90,
    MinusZ90,
    QubitRegister,
    Reset,
    Rx,
    Ry,
    Rz,
    U,
    Wait,
    X,
    Y,
    Z,
)
from opensquirrel.ir import Instruction
from opensquirrel.register_manager import DEFAULT_BIT_REGISTER_NAME, DEFAULT_QUBIT_REGISTER_NAME


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

    @pytest.mark.parametrize(
        ("builder", "expected_result"),
        [
            (CircuitBuilder(2, 2).I(0).X(0).Y(0).Z(0), [I(0), X(0), Y(0), Z(0)]),
            (
                CircuitBuilder(2, 2).X90(0).mX90(0).Y90(0).mY90(0).Z90(0).mZ90(0),
                [X90(0), MinusX90(0), Y90(0), MinusY90(0), Z90(0), MinusZ90(0)],
            ),
            (CircuitBuilder(2, 2).Rx(0, -1).Ry(1, 1).Rz(0, math.pi), [Rx(0, -1), Ry(1, 1), Rz(0, math.pi)]),
            (CircuitBuilder(2, 2).U(0, 1, 2, 3), [U(0, 1.0, 2.0, 3.0)]),
            (CircuitBuilder(2, 2).CZ(0, 1).CNOT(1, 0).SWAP(0, 1), [CZ(0, 1), CNOT(1, 0), SWAP(0, 1)]),
            (CircuitBuilder(2, 2).measure(0, 0).measure(1, 1), [Measure(0, 0), Measure(1, 1)]),
            (CircuitBuilder(2, 2).init(0).init(1), [Init(0), Init(1)]),
            (CircuitBuilder(2, 2).reset(0).reset(1), [Reset(0), Reset(1)]),
            (CircuitBuilder(2, 2).barrier(0).barrier(1), [Barrier(0), Barrier(1)]),
            (CircuitBuilder(2, 2).wait(0, 1).wait(1, 2), [Wait(0, 1), Wait(1, 2)]),
        ],
        ids=[
            "Pauli_gates",
            "pi/2-rotations",
            "rotation_gates",
            "u_gate",
            "two-qubit_gates",
            "measure",
            "init",
            "reset",
            "barrier",
            "wait",
        ],
    )
    def test_instructions(self, builder: CircuitBuilder, expected_result: list[Instruction]) -> None:
        circuit = builder.to_circuit()
        assert circuit.qubit_register_size == 2
        assert circuit.qubit_register_name == "q"
        assert circuit.bit_register_size == 2
        assert circuit.bit_register_name == "b"
        assert circuit.ir.statements == expected_result

    def test_chain(self) -> None:
        builder = CircuitBuilder(3)

        circuit = builder.H(0).CNOT(0, 1).to_circuit()

        assert circuit.ir.statements == [H(0), CNOT(0, 1)]

    def test_gate_index_error(self) -> None:
        builder = CircuitBuilder(2)

        with pytest.raises(IndexError, match="qubit index 12 is out of bounds"):
            builder.H(0).CNOT(0, 12).to_circuit()

    def test_measure_index_error(self) -> None:
        builder = CircuitBuilder(2, 1)
        with pytest.raises(IndexError, match="bit index 10 is out of bounds"):
            builder.H(0).measure(0, 10).to_circuit()

    def test_unknown_instruction(self) -> None:
        builder = CircuitBuilder(3)
        with pytest.raises(AttributeError, match="has no attribute 'unknown'"):
            builder.unknown(0)

    def test_wrong_number_of_arguments(self) -> None:
        builder = CircuitBuilder(3)

        with pytest.raises(TypeError, match="with the wrong number or type of arguments:"):
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

    def test_multiple_registers(self) -> None:
        builder = CircuitBuilder()
        q0 = QubitRegister(1, "q0")
        q1 = QubitRegister(1, "q1")
        b = BitRegister(2)

        builder.add_register(q0)
        builder.add_register(q1)
        builder.add_register(b)

        builder.H(q0[0])
        builder.H(0)

        builder.H(q1[0])
        builder.H(1)

        q2 = QubitRegister(2, "q2")
        builder.add_register(q2)
        builder.H(q2[-1])

        q3 = QubitRegister(3, "q3")
        builder.add_register(q3)
        builder.H(q3[-1])

        circuit = builder.to_circuit()

        assert circuit.ir.statements == [H(0), H(0), H(1), H(1), H(3), H(6)]
        assert (
            str(circuit)
            == """version 3.0

qubit[7] q
bit[2] b

H q[0]
H q[0]
H q[1]
H q[1]
H q[3]
H q[6]
"""
        )

    def test_initial_register_has_default_name(self) -> None:
        initial_qubit_register_size = 2
        initial_bit_register_size = 3

        builder = CircuitBuilder(initial_qubit_register_size, initial_bit_register_size)

        qubit_registry = builder.register_manager._qubit_registry
        bit_registry = builder.register_manager._bit_registry

        assert DEFAULT_QUBIT_REGISTER_NAME in qubit_registry
        assert DEFAULT_BIT_REGISTER_NAME in bit_registry

        assert qubit_registry[DEFAULT_QUBIT_REGISTER_NAME].size == initial_qubit_register_size
        assert bit_registry[DEFAULT_BIT_REGISTER_NAME].size == initial_bit_register_size

        with pytest.raises(KeyError, match=f"Qubit register with name '{DEFAULT_QUBIT_REGISTER_NAME}' already exists"):
            builder.add_register(QubitRegister(1, DEFAULT_QUBIT_REGISTER_NAME))

        with pytest.raises(KeyError, match=f"Bit register with name '{DEFAULT_BIT_REGISTER_NAME}' already exists"):
            builder.add_register(BitRegister(1, DEFAULT_BIT_REGISTER_NAME))

        builder.add_register(QubitRegister(1, DEFAULT_BIT_REGISTER_NAME))
        builder.add_register(BitRegister(1, DEFAULT_QUBIT_REGISTER_NAME))

        assert DEFAULT_BIT_REGISTER_NAME in qubit_registry
        assert DEFAULT_QUBIT_REGISTER_NAME in bit_registry

        assert builder.register_manager.qubit_register_name == DEFAULT_QUBIT_REGISTER_NAME
        assert builder.register_manager.bit_register_name == DEFAULT_BIT_REGISTER_NAME

        assert builder.register_manager.qubit_register_size == initial_qubit_register_size + 1
        assert builder.register_manager.bit_register_size == initial_bit_register_size + 1

    def test_empty_registers(self) -> None:
        builder = CircuitBuilder()

        assert builder.register_manager.qubit_register_name == DEFAULT_QUBIT_REGISTER_NAME
        assert builder.register_manager.bit_register_name == DEFAULT_BIT_REGISTER_NAME

        assert builder.register_manager.qubit_register_size == 0
        assert builder.register_manager.bit_register_size == 0

        builder.add_register(QubitRegister(1))
        builder.add_register(BitRegister(1))

    def test_register_index_out_of_range(self) -> None:
        q0_size = 3
        builder = CircuitBuilder(q0_size)

        q1_size = 2
        q1 = QubitRegister(q1_size, "q1")
        builder.add_register(q1)

        with pytest.raises(IndexError, match=f"Index {q1_size} is out of range"):
            builder.H(q1[q1_size])

        assert q1[0] == q0_size

    def test_logical_to_virtual_qubit(self) -> None:
        builder = CircuitBuilder()

        q1_size = 4
        q2_size = 43
        q3_size = 21

        q3 = QubitRegister(q3_size, "q3")
        q2 = QubitRegister(q2_size, "q2")
        q1 = QubitRegister(q1_size, "q1")

        builder.add_register(q1)
        builder.add_register(q2)
        builder.add_register(q3)

        q1_index = 3
        q2_index = 5
        q3_index = 9

        assert q1[q1_index] == q1_index
        assert q2[q2_index] == q1_size + q2_index
        assert q3[q3_index] == q1_size + q2_size + q3_index

    def test_simple_programmatic_circuit(self) -> None:
        builder = CircuitBuilder()

        q0_register = QubitRegister(6, "logical qubits")
        q1_register = QubitRegister(6, "ancilla qubits")

        builder.add_register(q0_register)
        builder.add_register(q1_register)

        for q0, q1 in zip(q0_register, q1_register, strict=True):
            builder.H(q0)
            k = q0 + 1
            builder.CRk(q1, q0, k)

        bits = BitRegister(6, "measurement bits")
        builder.add_register(bits)

        for q0, bit in zip(q0_register, bits, strict=True):
            builder.measure(q0, bit)

        circuit = builder.to_circuit()

        assert (
            str(circuit)
            == """version 3.0

qubit[12] q
bit[6] b

H q[0]
CRk(1) q[6], q[0]
H q[1]
CRk(2) q[7], q[1]
H q[2]
CRk(3) q[8], q[2]
H q[3]
CRk(4) q[9], q[3]
H q[4]
CRk(5) q[10], q[4]
H q[5]
CRk(6) q[11], q[5]
b[0] = measure q[0]
b[1] = measure q[1]
b[2] = measure q[2]
b[3] = measure q[3]
b[4] = measure q[4]
b[5] = measure q[5]
"""
        )

    def test_register_slice(self) -> None:
        size = 9
        q0 = QubitRegister(size, "q0")
        q1 = QubitRegister(size, "q1")
        q0_slice = [1, 3, 5, 7]
        q1_slice = [4, 5, 6]

        assert q0[1] == 1
        assert q1[1] == 1
        assert q0[1:8:2] == q0_slice
        assert q1[4:7:1] == q1_slice

        builder = CircuitBuilder()
        builder.add_register(q0)
        builder.add_register(q1)

        assert q0[1] == 1
        assert q1[1] == size + 1
        assert q0[1:8:2] == q0_slice
        assert q1[4:7:1] == [i + size for i in q1_slice]

    def test_register_negative_index(self) -> None:
        q0_size = 4
        q1_size = 11
        q0 = QubitRegister(q0_size, "q0")
        q1 = QubitRegister(q1_size, "q1")
        q0_neg_index = -1
        q1_neg_index = -2

        assert q0[-1] == q0_size + q0_neg_index
        assert q1[-2] == q1_size + q1_neg_index

        builder = CircuitBuilder()
        builder.add_register(q0)
        builder.add_register(q1)

        assert q0[-1] == q0_size + q0_neg_index
        assert q1[-2] == q0_size + q1_size + q1_neg_index
