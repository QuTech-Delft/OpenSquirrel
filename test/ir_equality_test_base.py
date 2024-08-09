from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
from numpy.typing import NDArray

from opensquirrel import Circuit, circuit_matrix_calculator
from opensquirrel.common import are_matrices_equivalent_up_to_global_phase


def check_equivalence_up_to_global_phase(matrix_a: NDArray[np.complex128], matrix_b: NDArray[np.complex128]) -> None:
    assert are_matrices_equivalent_up_to_global_phase(matrix_a, matrix_b)


def modify_circuit_and_check(
    circuit: Circuit, action: Callable[[Circuit, Any]], expected_circuit: Circuit | None = None
) -> None:
    """
    Checks whether the action preserves:
    - the number of qubits,
    - the qubit register name(s),
    - the circuit matrix up to a global phase factor.
    """
    # Store matrix before decompositions.
    expected_matrix = circuit_matrix_calculator.get_circuit_matrix(circuit)

    action(circuit)

    # Get matrix after decompositions.
    actual_matrix = circuit_matrix_calculator.get_circuit_matrix(circuit)

    check_equivalence_up_to_global_phase(actual_matrix, expected_matrix)

    if expected_circuit is not None:
        assert circuit == expected_circuit
