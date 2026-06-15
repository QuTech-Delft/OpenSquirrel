import re
from math import pi

import pytest

from opensquirrel import (
    CNOT,
    CR,
    CV,
    CY,
    CZ,
    DCNOT,
    ECR,
    ISWAP,
    MS,
    SWAP,
    X90,
    Y90,
    Z90,
    Barrier,
    BitRegister,
    CircuitBuilder,
    CRk,
    H,
    I,
    Init,
    InvSqrtSWAP,
    M,
    Measure,
    MinusX90,
    MinusY90,
    MinusZ90,
    QubitRegister,
    Reset,
    Rx,
    Ry,
    Rz,
    SqrtISWAP,
    SqrtSWAP,
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
            (CircuitBuilder(2, 2).Rx(0, -1).Ry(1, 1).Rz(0, pi), [Rx(0, -1), Ry(1, 1), Rz(0, pi)]),
            (CircuitBuilder(2, 2).U(0, 1, 2, 3), [U(0, 1.0, 2.0, 3.0)]),
            (
                CircuitBuilder(2, 2).CNOT(0, 1).CZ(0, 1).CR(0, 1, pi / 2).CRk(0, 1, 2).CV(0, 1).CY(0, 1),
                [CNOT(0, 1), CZ(0, 1), CR(0, 1, pi / 2), CRk(0, 1, 2), CV(0, 1), CY(0, 1)],
            ),
            (
                CircuitBuilder(2, 2).InvSqrtSWAP(0, 1).ISWAP(0, 1).SqrtISWAP(0, 1).SqrtSWAP(0, 1).SWAP(0, 1),
                [InvSqrtSWAP(0, 1), ISWAP(0, 1), SqrtISWAP(0, 1), SqrtSWAP(0, 1), SWAP(0, 1)],
            ),
            (CircuitBuilder(2, 2).DCNOT(0, 1).ECR(0, 1).M(0, 1).MS(0, 1), [DCNOT(0, 1), ECR(0, 1), M(0, 1), MS(0, 1)]),
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
            "controlled_gates",
            "swap_gates",
            "additional_2_qubit_gates",
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

        msg = re.escape(f"qubit register with name {DEFAULT_QUBIT_REGISTER_NAME!r} already exists")
        with pytest.raises(KeyError, match=msg):
            builder.add_register(QubitRegister(1, DEFAULT_QUBIT_REGISTER_NAME))

        msg = re.escape(f"bit register with name {DEFAULT_BIT_REGISTER_NAME!r} already exists")
        with pytest.raises(KeyError, match=msg):
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

        with pytest.raises(IndexError, match=f"index {q1_size!r} is out of range"):
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


class TestSGMQNotation:
    def test_sgmq_list(self) -> None:
        builder = CircuitBuilder(3)
        builder.H([0, 1, 2])
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [H(0), H(1), H(2)]

    def test_sgmq_register(self) -> None:
        builder = CircuitBuilder()
        q0 = QubitRegister(3, "q0")
        builder.add_register(q0)
        builder.H(q0)
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [H(0), H(1), H(2)]

    def test_sgmq_multiple_registers(self) -> None:
        builder = CircuitBuilder()
        q0 = QubitRegister(3, "q0")
        q1 = QubitRegister(2, "q1")
        builder.add_register(q0)
        builder.add_register(q1)

        builder.H(q0)
        builder.H(q1)

        circuit = builder.to_circuit()

        assert circuit.ir.statements == [H(0), H(1), H(2), H(3), H(4)]

    def test_sgmq_parametric_gate(self) -> None:
        builder = CircuitBuilder(3)
        builder.Rx([0, 1, 2], pi / 2)
        builder.U([0, 1], 1.0, 2.0, 3.0)
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [
            Rx(0, pi / 2),
            Rx(1, pi / 2),
            Rx(2, pi / 2),
            U(0, 1.0, 2.0, 3.0),
            U(1, 1.0, 2.0, 3.0),
        ]

    def test_sgmq_parametric_register(self) -> None:
        builder = CircuitBuilder()
        q0 = QubitRegister(2, "q0")
        builder.add_register(q0)
        builder.Ry(q0, 1.5)
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [Ry(0, 1.5), Ry(1, 1.5)]

    def test_sgmq_measure(self) -> None:
        builder = CircuitBuilder(3, 2)
        builder.measure([1, 2], [0, 1])
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [Measure(1, 0), Measure(2, 1)]

    def test_sgmq_measure_registers(self) -> None:
        builder = CircuitBuilder()
        q0 = QubitRegister(2, "q0")
        b0 = BitRegister(2, "b0")
        builder.add_register(q0)
        builder.add_register(b0)

        builder.measure(q0, b0)
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [Measure(0, 0), Measure(1, 1)]

    def test_sgmq_measure_slice(self) -> None:
        builder = CircuitBuilder()
        q0 = QubitRegister(3, "q0")
        b0 = BitRegister(4, "b0")
        builder.add_register(q0)
        builder.add_register(b0)

        builder.measure(q0[0:2], b0[1:3])
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [Measure(0, 1), Measure(1, 2)]

    def test_sgmq_measure_error(self) -> None:
        builder = CircuitBuilder(3, 2)

        with pytest.raises(ValueError, match="SGMQ requires matching operand lengths: got 3 and 2"):
            builder.measure([0, 1, 2], [0, 1])

    def test_sgmq_measure_register_error(self) -> None:
        builder = CircuitBuilder()
        q0 = QubitRegister(3, "q0")
        b0 = BitRegister(2, "b0")
        builder.add_register(q0)
        builder.add_register(b0)

        with pytest.raises(ValueError, match="SGMQ requires matching operand lengths: got 3 and 2"):
            builder.measure(q0, b0)

    def test_sgmq_init_reset(self) -> None:
        builder = CircuitBuilder(3)
        builder.init([0, 1, 2])
        builder.reset([0, 1, 2])
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [Init(0), Init(1), Init(2), Reset(0), Reset(1), Reset(2)]

    def test_sgmq_barrier_wait(self) -> None:
        builder = CircuitBuilder(3)
        builder.barrier([0, 1, 2])
        builder.wait([0, 1], 10)
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [Barrier(0), Barrier(1), Barrier(2), Wait(0, 10), Wait(1, 10)]

    def test_sgmq_mixed_with_regular_calls(self) -> None:
        builder = CircuitBuilder(4)
        builder.H([0, 1])
        builder.X(2)
        builder.Y([3])
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [H(0), H(1), X(2), Y(3)]

    def test_sgmq_empty_list(self) -> None:
        builder = CircuitBuilder(3)
        builder.H([])
        circuit = builder.to_circuit()

        assert circuit.ir.statements == []

    def test_sgmq_chaining(self) -> None:
        circuit = CircuitBuilder(3).H([0, 1]).X([2]).to_circuit()

        assert circuit.ir.statements == [H(0), H(1), X(2)]

    def test_sgmq_out_of_bounds_error(self) -> None:
        builder = CircuitBuilder(3)

        with pytest.raises(IndexError, match="qubit index 10 is out of bounds"):
            builder.H([0, 1, 10])

    def test_sgmq_two_qubit_gates(self) -> None:
        builder = CircuitBuilder(4)
        builder.CNOT([0, 1], [2, 3])
        builder.SWAP([0, 1], [2, 3])
        builder.CZ([0, 1], [2, 3])
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [CNOT(0, 2), CNOT(1, 3), SWAP(0, 2), SWAP(1, 3), CZ(0, 2), CZ(1, 3)]

    def test_sgmq_two_qubit_error(self) -> None:
        builder = CircuitBuilder(4)

        with pytest.raises(
            ValueError,
            match=(
                "SGMQ notation for multi-operand instructions requires operands to be "
                "lists or registers \\(and of equal length\\)"
            ),
        ):
            builder.CNOT([0, 1, 2], 3)

    def test_sgmq_two_qubit_different_operand_types(self) -> None:
        builder = CircuitBuilder(2)
        q0 = QubitRegister(2, "q0")
        builder.add_register(q0)
        builder.CNOT([0, 1], q0)
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [CNOT(0, 2), CNOT(1, 3)]

    def test_sgmq_length_mismatch(self) -> None:
        builder = CircuitBuilder(4)

        with pytest.raises(ValueError, match="SGMQ requires matching operand lengths: got 3 and 2"):
            builder.CNOT([0, 1, 2], [1, 2])


class TestAddInstruction:
    def test_add_single_instruction(self) -> None:
        builder = CircuitBuilder(2)
        builder.add_instruction(H(0))
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [H(0)]

    def test_add_multiple_instructions(self) -> None:
        builder = CircuitBuilder(2)
        builder.add_instruction([H(0), CNOT(0, 1)])
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [H(0), CNOT(0, 1)]

    def test_add_multiple_parametric_instructions(self) -> None:
        builder = CircuitBuilder(4)
        builder.add_instruction(Rz(i, pi / 2 ** (i + 1)) for i in range(4))
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [Rz(i, pi / 2 ** (i + 1)) for i in range(4)]

    def test_add_instruction_chaining(self) -> None:
        builder = CircuitBuilder(2)
        circuit = builder.add_instruction(H(0)).add_instruction(CNOT(0, 1)).to_circuit()

        assert circuit.ir.statements == [H(0), CNOT(0, 1)]

    def test_add_instruction_mixed_with_plain_builder_calls(self) -> None:
        builder = CircuitBuilder(3)
        builder.H(0)
        builder.add_instruction(CNOT(0, 1))
        builder.H(2)
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [H(0), CNOT(0, 1), H(2)]

    def test_add_instruction_out_of_bounds_qubit(self) -> None:
        builder = CircuitBuilder(2)

        with pytest.raises(IndexError, match="qubit index 5 is out of bounds"):
            builder.add_instruction(H(5))

    def test_add_instruction_out_of_bounds_bit(self) -> None:
        builder = CircuitBuilder(2, 2)

        with pytest.raises(IndexError, match="bit index 10 is out of bounds"):
            builder.add_instruction(Measure(0, 10))

    def test_add_empty_list(self) -> None:
        builder = CircuitBuilder(2)
        builder.add_instruction([])
        circuit = builder.to_circuit()

        assert circuit.ir.statements == []

    @pytest.mark.parametrize(
        ("instruction", "expected"),
        [
            (Measure(0, 0), Measure(0, 0)),
            (Init(0), Init(0)),
            (Reset(0), Reset(0)),
            (Barrier(0), Barrier(0)),
            (Wait(0, 10), Wait(0, 10)),
        ],
        ids=[
            "measure",
            "init",
            "reset",
            "barrier",
            "wait",
        ],
    )
    def test_add_instruction_non_unitaries(self, instruction: Instruction, expected: Instruction) -> None:
        builder = CircuitBuilder(2, 2)
        builder.add_instruction(instruction)
        circuit = builder.to_circuit()

        assert circuit.ir.statements == [expected]
