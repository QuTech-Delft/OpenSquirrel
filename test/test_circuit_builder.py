import math

import numpy as np
import pytest
from numpy.typing import NDArray

from opensquirrel import CNOT, CZ, SWAP, H, I, Rx, Ry, Rz, X, Y, Z
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
from opensquirrel.ir import Barrier, Init, Instruction, Measure, Reset, Wait


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
            (CircuitBuilder(2, 2).Rx(0, -1).Ry(1, 1).Rz(0, math.pi), [Rx(0, -1), Ry(1, 1), Rz(0, math.pi)]),
            (CircuitBuilder(2, 2).CZ(0, 1).CNOT(1, 0).SWAP(0, 1), [CZ(0, 1), CNOT(1, 0), SWAP(0, 1)]),
            (CircuitBuilder(2, 2).measure(0, 0).measure(1, 1), [Measure(0, 0), Measure(1, 1)]),
            (CircuitBuilder(2, 2).init(0).init(1), [Init(0), Init(1)]),
            (CircuitBuilder(2, 2).reset(0).reset(1), [Reset(0), Reset(1)]),
            (CircuitBuilder(2, 2).barrier(0).barrier(1), [Barrier(0), Barrier(1)]),
            (CircuitBuilder(2, 2).wait(0, 1).wait(1, 2), [Wait(0, 1), Wait(1, 2)]),
        ],
        ids=["Pauli_gates", "rotation_gates", "two-qubit_gates", "measure", "init", "reset", "barrier", "wait"],
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

    @pytest.mark.parametrize(
        ("can_circuit_matrix", "expected_matrix"),
        [
            (
                get_circuit_matrix(CircuitBuilder(2).Can(0, 1, [-1 / 4, -1 / 4, 1 / 4]).to_circuit()),
                get_circuit_matrix(CircuitBuilder(2).Z(0).Can(0, 1, [1 / 4, 1 / 4, 1 / 4]).Z(0).to_circuit()),
            ),
            (
                get_circuit_matrix(CircuitBuilder(2).Can(0, 1, [2 / 3 - 1, 1 / 4, 1 / 4]).to_circuit()),
                get_circuit_matrix(CircuitBuilder(2).Y(0).Y(1).Can(0, 1, [2 / 3, 1 / 4, 1 / 4]).Z(0).Z(1).to_circuit()),
            ),
            (
                get_circuit_matrix(CircuitBuilder(2).Can(0, 1, [1 / 4, 1 / 4, 1 / 4]).to_circuit()),
                get_circuit_matrix(
                    CircuitBuilder(2).S(0).S(1).Can(0, 1, [1 / 4, 1 / 4, 1 / 4]).Sdag(0).Sdag(1).to_circuit()
                ),
            ),
            (
                get_circuit_matrix(CircuitBuilder(2).Can(0, 1, [1 - 1 / 2, 1 / 2, 0]).to_circuit()),
                get_circuit_matrix(CircuitBuilder(2).Y(1).Can(0, 1, [1 / 2, 1 / 2, 0]).Z(0).Y(0).Z(1).to_circuit()),
            ),
        ],
        ids=["Y_and_Z", "two_Z", "S_S_dagger", "asymmetric_Y_Z_Y"],
    )
    def test_can_circuit(
        self, can_circuit_matrix: NDArray[np.complex128], expected_matrix: NDArray[np.complex128]
    ) -> None:
        assert are_matrices_equivalent_up_to_global_phase(can_circuit_matrix, expected_matrix)
