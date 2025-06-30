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
        qubit_register_size: int,
        connectivity: dict[str, list[int]],
        timeout: float | None = None,
        **kwargs: Any,
    ) -> None:
        self.qubit_register_size = qubit_register_size
        self.connectivity = connectivity
        self.timeout = timeout
        self.distance_matrix = self._get_distance(connectivity, qubit_register_size)
        super().__init__(qubit_register_size, None, **kwargs)

    def map(self, ir: IR) -> Mapping:
        """
        Find an initial mapping of virtual qubits to physical qubits that minimizes
        the sum of distances between mapped operands of all two-qubit gates, using
        Mixed Integer Programming (MIP).

        This method formulates the mapping as a linear assignment problem, where the
        objective is to minimize the total "distance cost" of executing all two-qubit
        gates, given the connectivity.

        Args:
            ir (IR): The intermediate representation of the quantum circuit to be mapped.

        Returns:
            Mapping: Mapping from virtual to physical qubits.

        Raises:
            RuntimeError: If the MIP solver fails to find a feasible mapping or times out.
            RuntimeError: If the number of virtual qubits exceeds the number of physical qubits.
        """
        n = self.qubit_register_size
        distance = self.distance_matrix

        self._validate_logical_vs_physical_qubits(ir, n)
        cost = self._get_cost(ir, distance, n)
        constraints, integrality, bounds = self._get_constraints(n)
        milp_options = self._get_milp_options()
        mapping = self._solve_and_extract_mapping(cost, constraints, integrality, bounds, milp_options, n)
        return Mapping(mapping)

    @staticmethod
    def _get_distance(connectivity: dict[str, list[int]], qubit_register_size: int) -> list[list[int]]:
        distance = np.full((qubit_register_size, qubit_register_size), DISTANCE_UL, dtype=int)
        np.fill_diagonal(distance, 0)
        for start_qubit_index, end_qubit_indices in connectivity.items():
            for end_qubit_index in end_qubit_indices:
                distance[int(start_qubit_index), end_qubit_index] = 1
        for k in range(qubit_register_size):
            for i in range(qubit_register_size):
                for j in range(qubit_register_size):
                    if distance[i][j] > distance[i][k] + distance[k][j]:
                        distance[i][j] = distance[i][k] + distance[k][j]
        return list(distance)

    def _validate_logical_vs_physical_qubits(self, ir: IR, qubit_register_size: int) -> None:
        # Fail fast: if the number of virtual qubits exceeds the number of physical qubits
        max_virtual_index = max(
            (
                q.index
                for statement in getattr(ir, "statements", [])
                if isinstance(statement, Instruction)
                for q in getattr(statement, "arguments", [])
                if isinstance(q, Qubit)
            ),
            default=-1,
        )
        if max_virtual_index >= qubit_register_size:
            error_message = (
                f"Number of virtual qubits ({max_virtual_index + 1}) exceeds "
                f"number of physical qubits ({qubit_register_size})"
            )
            raise RuntimeError(error_message)

    def _get_cost(self, ir: IR, distance: list[list[int]], qubit_register_size: int) -> list[list[int]]:
        reference_counter = [[0 for _ in range(qubit_register_size)] for _ in range(qubit_register_size)]
        for statement in getattr(ir, "statements", []):
            if isinstance(statement, Instruction):
                args = statement.arguments
                if args and len(args) > 1 and all(isinstance(arg, Qubit) for arg in args):
                    qubit_args = [arg for arg in args if isinstance(arg, Qubit)]
                    for q_0, q_1 in zip(qubit_args[:-1], qubit_args[1:]):
                        reference_counter[q_0.index][q_1.index] += 1
                        reference_counter[q_1.index][q_0.index] += 1
        cost = [[0 for _ in range(qubit_register_size)] for _ in range(qubit_register_size)]
        for i in range(qubit_register_size):
            for k in range(qubit_register_size):
                cost[i][k] = sum(
                    reference_counter[i][j] * distance[k][m]
                    for j in range(qubit_register_size)
                    for m in range(qubit_register_size)
                )
        return cost

    def _get_constraints(self, qubit_register_size: int) -> tuple[list[LinearConstraint], list[bool], Bounds]:
        num_vars = qubit_register_size * qubit_register_size
        eq_a = np.zeros((qubit_register_size, num_vars))
        for q_i in range(qubit_register_size):
            for q_k in range(qubit_register_size):
                eq_a[q_i, q_i * qubit_register_size + q_k] = 1
        eq_b = np.ones(qubit_register_size)

        ub_a = np.zeros((qubit_register_size, num_vars))
        for q_k in range(qubit_register_size):
            for q_i in range(qubit_register_size):
                ub_a[q_k, q_i * qubit_register_size + q_k] = 1
        ub_b = np.ones(qubit_register_size)
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
        qubit_register_size: int,
    ) -> list[int]:
        cost = np.array(cost_matrix).flatten()
        res = milp(c=cost, constraints=constraints, integrality=integrality, bounds=bounds, options=milp_options)
        if not res.success:
            error_message = (
                f"MIP solver failed to find a feasible mapping. Status: {res.status}, Message: {res.message}"
            )
            raise RuntimeError(error_message)
        x_sol = res.x.reshape((qubit_register_size, qubit_register_size))
        mapping = []
        for q_i in range(qubit_register_size):
            k = int(np.argmax(x_sol[q_i]))
            mapping.append(k)
        return mapping
