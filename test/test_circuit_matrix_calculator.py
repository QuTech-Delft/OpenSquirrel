import numpy as np
import pytest
from numpy.typing import ArrayLike

from opensquirrel import CircuitBuilder
from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from opensquirrel.ir import Qubit


@pytest.mark.parametrize(
    "builder, expected_matrix",
    [
        (CircuitBuilder(1).H(Qubit(0)), np.sqrt(0.5) * np.array([[1, 1], [1, -1]])),
        (CircuitBuilder(1).H(Qubit(0)).H(Qubit(0)), np.eye(2)),
        (CircuitBuilder(1).H(Qubit(0)).H(Qubit(0)).H(Qubit(0)), np.sqrt(0.5) * np.array([[1, 1], [1, -1]])),
        (
            CircuitBuilder(2).H(Qubit(0)).X(Qubit(1)),
            np.sqrt(0.5) * np.array([[0, 0, 1, 1], [0, 0, 1, -1], [1, 1, 0, 0], [1, -1, 0, 0]]),
        ),
        (
            CircuitBuilder(2).H(Qubit(1)).X(Qubit(0)),
            np.sqrt(0.5) * np.array([[0, 1, 0, 1], [1, 0, 1, 0], [0, 1, 0, -1], [1, 0, -1, 0]]),
        ),
        (CircuitBuilder(2).CNOT(Qubit(1), Qubit(0)), [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]),
        (CircuitBuilder(2).CNOT(Qubit(0), Qubit(1)), [[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]]),
        (
            CircuitBuilder(2).H(Qubit(0)).CNOT(Qubit(0), Qubit(1)),
            np.sqrt(0.5) * np.array([[1, 1, 0, 0], [0, 0, 1, -1], [0, 0, 1, 1], [1, -1, 0, 0]]),
        ),
        (
            CircuitBuilder(3).H(Qubit(0)).CNOT(Qubit(0), Qubit(2)),
            np.sqrt(0.5)
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
        ),
    ],
    ids=[
        "H[0]",
        "H[0]H[0]",
        "H[0]H[0]H[0]",
        "H[0]X[1]",
        "H[1]X[0]",
        "CNOT[1,0]",
        "CNOT[0,1]",
        "H[0]CNOT[0,1]",
        "H[0]CNOT[0,2]",
    ],
)
def test_get_circuit_matrix(builder: CircuitBuilder, expected_matrix: ArrayLike) -> None:
    circuit = builder.to_circuit()
    matrix = get_circuit_matrix(circuit)
    np.testing.assert_almost_equal(matrix, expected_matrix)
