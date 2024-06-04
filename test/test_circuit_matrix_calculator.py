import math

import numpy as np

from opensquirrel import circuit_matrix_calculator
from opensquirrel.circuit import Circuit
from opensquirrel.default_gates import CNOT, H, X
from opensquirrel.ir import IR, Qubit
from opensquirrel.register_manager import RegisterManager


def test_hadamard() -> None:
    register_manager = RegisterManager(qubit_register_size=1)
    ir = IR()
    ir.add_gate(H(Qubit(0)))
    circuit = Circuit(register_manager, ir)

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit), math.sqrt(0.5) * np.array([[1, 1], [1, -1]])
    )


def test_double_hadamard() -> None:
    register_manager = RegisterManager(qubit_register_size=1)
    ir = IR()
    ir.add_gate(H(Qubit(0)))
    ir.add_gate(H(Qubit(0)))
    circuit = Circuit(register_manager, ir)

    np.testing.assert_almost_equal(circuit_matrix_calculator.get_circuit_matrix(circuit), np.eye(2))


def test_triple_hadamard() -> None:
    register_manager = RegisterManager(qubit_register_size=1)
    ir = IR()
    ir.add_gate(H(Qubit(0)))
    ir.add_gate(H(Qubit(0)))
    ir.add_gate(H(Qubit(0)))
    circuit = Circuit(register_manager, ir)

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit), math.sqrt(0.5) * np.array([[1, 1], [1, -1]])
    )


def test_hadamard_x() -> None:
    register_manager = RegisterManager(qubit_register_size=2)
    ir = IR()
    ir.add_gate(H(Qubit(0)))
    ir.add_gate(X(Qubit(1)))
    circuit = Circuit(register_manager, ir)

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit),
        math.sqrt(0.5) * np.array([[0, 0, 1, 1], [0, 0, 1, -1], [1, 1, 0, 0], [1, -1, 0, 0]]),
    )


def test_x_hadamard() -> None:
    register_manager = RegisterManager(qubit_register_size=2)
    ir = IR()
    ir.add_gate(H(Qubit(1)))
    ir.add_gate(X(Qubit(0)))
    circuit = Circuit(register_manager, ir)

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit),
        math.sqrt(0.5) * np.array([[0, 1, 0, 1], [1, 0, 1, 0], [0, 1, 0, -1], [1, 0, -1, 0]]),
    )


def test_cnot() -> None:
    register_manager = RegisterManager(qubit_register_size=2)
    ir = IR()
    ir.add_gate(CNOT(Qubit(1), Qubit(0)))
    circuit = Circuit(register_manager, ir)

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit), [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]
    )


def test_cnot_reversed() -> None:
    register_manager = RegisterManager(qubit_register_size=2)
    ir = IR()
    ir.add_gate(CNOT(Qubit(0), Qubit(1)))
    circuit = Circuit(register_manager, ir)

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit), [[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]]
    )


def test_hadamard_cnot() -> None:
    register_manager = RegisterManager(qubit_register_size=2)
    ir = IR()
    ir.add_gate(H(Qubit(0)))
    ir.add_gate(CNOT(Qubit(0), Qubit(1)))
    circuit = Circuit(register_manager, ir)

    np.testing.assert_almost_equal(
        circuit_matrix_calculator.get_circuit_matrix(circuit),
        math.sqrt(0.5) * np.array([[1, 1, 0, 0], [0, 0, 1, -1], [0, 0, 1, 1], [1, -1, 0, 0]]),
    )


def test_hadamard_cnot_0_2() -> None:
    register_manager = RegisterManager(qubit_register_size=3)
    ir = IR()
    ir.add_gate(H(Qubit(0)))
    ir.add_gate(CNOT(Qubit(0), Qubit(2)))
    circuit = Circuit(register_manager, ir)

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
