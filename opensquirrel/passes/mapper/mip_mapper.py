# OpenQL MIP-Like Mapper
from __future__ import annotations

from typing import Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from opensquirrel.ir import IR, Instruction, Qubit
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping

DISTANCE_UL = 999999


class MIPMapper(Mapper):
    def __init__(
        self,
        connectivity: dict[str, list[int]],
        timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.connectivity = connectivity
        self.timeout = timeout

    def map(self, ir: IR, qubit_register_size: int) -> Mapping:
        """
        Find an initial mapping of virtual qubits to physical qubits that minimizes
        the sum of distances between mapped operands of all two-qubit gates, using
        Mixed Integer Programming (MIP).

        This method formulates the mapping as a linear assignment problem, where the
        objective is to minimize the total "distance cost" of executing all two-qubit
        gates, given the connectivity.

        Args:
            ir (IR): The intermediate representation of the quantum circuit to be mapped.
            qubit_register_size (int): The number of virtual qubits in the circuit.

        Returns:
            Mapping: Mapping from virtual to physical qubits.

        Raises:
            RuntimeError: If the MIP solver fails to find a feasible mapping or times out.
            RuntimeError: If the number of virtual qubits exceeds the number of physical qubits.
        """
        num_physical_qubits = len(self.connectivity)

        if qubit_register_size > num_physical_qubits:
            error_message = (
                f"Number of virtual qubits ({qubit_register_size}) exceeds "
                f"number of physical qubits ({num_physical_qubits})"
            )
            raise RuntimeError(error_message)

        distance = self._get_distance(self.connectivity)
        cost = self._get_cost(ir, distance, qubit_register_size, num_physical_qubits)
        constraints, integrality, bounds = self._get_constraints(qubit_register_size, num_physical_qubits)
        milp_options = self._get_milp_options()
        mapping = self._solve_and_extract_mapping(
            cost, constraints, integrality, bounds, milp_options, qubit_register_size, num_physical_qubits
        )
        return Mapping(mapping)

    @staticmethod
    def _get_distance(connectivity: dict[str, list[int]]) -> list[list[int]]:
        num_physical_qubits = len(connectivity)
        distance = np.full((num_physical_qubits, num_physical_qubits), DISTANCE_UL, dtype=int)
        np.fill_diagonal(distance, 0)

        for start_qubit_index, end_qubit_indices in connectivity.items():
            for end_qubit_index in end_qubit_indices:
                distance[int(start_qubit_index), end_qubit_index] = 1

        for k in range(num_physical_qubits):
            for i in range(num_physical_qubits):
                for j in range(num_physical_qubits):
                    if distance[i][j] > distance[i][k] + distance[k][j]:
                        distance[i][j] = distance[i][k] + distance[k][j]

        return list(distance)

    def _get_cost(
        self, ir: IR, distance: list[list[int]], num_virtual_qubits: int, num_physical_qubits: int
    ) -> list[list[int]]:
        reference_counter = [[0 for _ in range(num_virtual_qubits)] for _ in range(num_virtual_qubits)]
        for statement in getattr(ir, "statements", []):
            if isinstance(statement, Instruction):
                args = statement.arguments
                if args and len(args) > 1 and all(isinstance(arg, Qubit) for arg in args):
                    qubit_args = [arg for arg in args if isinstance(arg, Qubit)]
                    for q_0, q_1 in zip(qubit_args[:-1], qubit_args[1:]):
                        reference_counter[q_0.index][q_1.index] += 1
                        reference_counter[q_1.index][q_0.index] += 1
        cost = [[0 for _ in range(num_physical_qubits)] for _ in range(num_virtual_qubits)]
        for i in range(num_virtual_qubits):
            for k in range(num_physical_qubits):
                cost[i][k] = sum(
                    reference_counter[i][j] * distance[k][l]
                    for j in range(num_virtual_qubits)
                    for l in range(num_physical_qubits)  # noqa: E741
                )
        return cost

    def _get_constraints(
        self, num_virtual_qubits: int, num_physical_qubits: int
    ) -> tuple[list[LinearConstraint], list[bool], Bounds]:
        num_vars = num_virtual_qubits * num_physical_qubits
        eq_a = np.zeros((num_virtual_qubits, num_vars))
        for q_i in range(num_virtual_qubits):
            for q_k in range(num_physical_qubits):
                eq_a[q_i, q_i * num_physical_qubits + q_k] = 1
        eq_b = np.ones(num_virtual_qubits)
        ub_a = np.zeros((num_physical_qubits, num_vars))
        for q_k in range(num_physical_qubits):
            for q_i in range(num_virtual_qubits):
                ub_a[q_k, q_i * num_physical_qubits + q_k] = 1
        ub_b = np.ones(num_physical_qubits)
        integrality = np.ones(num_vars, dtype=bool)
        bounds = Bounds(0, 1)
        constraints = [LinearConstraint(eq_a, eq_b, eq_b), LinearConstraint(ub_a, -np.inf, ub_b)]
        return constraints, list(integrality), bounds

    def _get_milp_options(self) -> dict[str, float]:
        milp_options = {}
        if self.timeout is not None:
            milp_options["time_limit"] = self.timeout
        return milp_options

    def _solve_and_extract_mapping(
        self,
        cost_matrix: list[list[int]],
        constraints: list[LinearConstraint],
        integrality: list[bool],
        bounds: Bounds,
        milp_options: dict[str, float],
        num_virtual_qubits: int,
        num_physical_qubits: int,
    ) -> list[int]:
        cost = np.array(cost_matrix).flatten()

        res = milp(c=cost, constraints=constraints, integrality=integrality, bounds=bounds, options=milp_options)

        if not res.success:
            error_message = (
                f"MIP solver failed to find a feasible mapping. Status: {res.status}, Message: {res.message}"
            )
            raise RuntimeError(error_message)

        x_sol = res.x.reshape((num_virtual_qubits, num_physical_qubits))
        mapping = []
        for q_i in range(num_virtual_qubits):
            q_k = int(np.argmax(x_sol[q_i]))
            mapping.append(q_k)

        return mapping
