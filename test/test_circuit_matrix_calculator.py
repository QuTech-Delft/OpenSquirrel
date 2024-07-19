import math

import numpy as np

from opensquirrel import Circuit, CircuitBuilder, circuit_matrix_calculator
from opensquirrel.default_gates import CNOT, H, X
from opensquirrel.ir import Qubit
from opensquirrel.register_manager import QubitRegister, RegisterManager


def test_hadamard() -> None:
    builder = CircuitBuilder(1)
    builder.H(Qubit(0))
    circuit = builder.to_circuit()

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit), math.sqrt(0.5) * np.array([[1, 1], [1, -1]])
    )


def test_double_hadamard() -> None:
    builder = CircuitBuilder(1)
    builder.H(Qubit(0))
    builder.H(Qubit(0))
    circuit = builder.to_circuit()

    np.testing.assert_almost_equal(circuit_matrix_calculator.get_circuit_matrix(circuit), np.eye(2))


def test_triple_hadamard() -> None:
    builder = CircuitBuilder(1)
    builder.H(Qubit(0))
    builder.H(Qubit(0))
    builder.H(Qubit(0))
    circuit = builder.to_circuit()

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit), math.sqrt(0.5) * np.array([[1, 1], [1, -1]])
    )


def test_hadamard_x() -> None:
    builder = CircuitBuilder(2)
    builder.H(Qubit(0))
    builder.X(Qubit(1))
    circuit = builder.to_circuit()
    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit),
        math.sqrt(0.5) * np.array([[0, 0, 1, 1], [0, 0, 1, -1], [1, 1, 0, 0], [1, -1, 0, 0]]),
    )


def test_x_hadamard() -> None:
    builder = CircuitBuilder(2)
    builder.H(Qubit(1))
    builder.X(Qubit(0))
    circuit = builder.to_circuit()

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit),
        math.sqrt(0.5) * np.array([[0, 1, 0, 1], [1, 0, 1, 0], [0, 1, 0, -1], [1, 0, -1, 0]]),
    )


def test_cnot() -> None:
    builder = CircuitBuilder(2)
    builder.CNOT(Qubit(1), Qubit(0))
    circuit = builder.to_circuit()

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit), [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]
    )


def test_cnot_reversed() -> None:
    builder = CircuitBuilder(2)
    builder.CNOT(Qubit(0), Qubit(1))
    circuit = builder.to_circuit()

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit), [[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]]
    )


def test_hadamard_cnot() -> None:
    builder = CircuitBuilder(2)
    builder.H(Qubit(0))
    builder.CNOT(Qubit(0), Qubit(1))
    circuit = builder.to_circuit()

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit),
        math.sqrt(0.5) * np.array([[1, 1, 0, 0], [0, 0, 1, -1], [0, 0, 1, 1], [1, -1, 0, 0]]),
    )


def test_hadamard_cnot_0_2() -> None:
    builder = CircuitBuilder(3)
    builder.H(Qubit(0))
    builder.CNOT(Qubit(0), Qubit(2))
    circuit = builder.to_circuit()

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit),
        math.sqrt(0.5)
        * np.array(
            [
                [1, 1, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 1, -1, 0, 0],
                [0, 0, 1, 1, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, -1],
                [0, 0, 0, 0, 1, 1, 0, 0],
                [1, -1, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 1, 1],
                [0, 0, 1, -1, 0, 0, 0, 0],
            ]
        ),
    )
