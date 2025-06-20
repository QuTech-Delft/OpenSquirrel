# OpenQL MIP-Like Mapper
from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import Bounds, LinearConstraint, milp

from opensquirrel.ir import IR, Instruction, Qubit
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping


def compute_distance_matrix(connectivity: dict[str, list[int]], n: int) -> NDArray[np.int_]:
    distance = np.full((n, n), 999999, dtype=int)
    np.fill_diagonal(distance, 0)
    for start_qubit_index, end_qubit_indices in connectivity.items():
        for end_qubit_index in end_qubit_indices:
            distance[int(start_qubit_index), end_qubit_index] = 1
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if distance[i, j] > distance[i, k] + distance[k, j]:
                    distance[i, j] = distance[i, k] + distance[k, j]
    return distance


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
        self.distance_matrix = compute_distance_matrix(connectivity, qubit_register_size)
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
        refcount = self.build_refcount(ir, n)
        cost_matrix = self.build_cost_matrix(refcount, distance, n)
        constraints, integrality, bounds = self.build_constraints(n)
        milp_options = self.build_milp_options()
        mapping = self.solve_and_extract_mapping(cost_matrix, constraints, integrality, bounds, milp_options, n)
        return Mapping(mapping)

    def _validate_logical_vs_physical_qubits(self, ir: IR, n: int) -> None:
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
        if max_virtual_index >= n:
            error_message = (
                f"Number of virtual qubits ({max_virtual_index + 1}) exceeds number of physical qubits ({n})"
            )
            raise RuntimeError(error_message)

    def build_refcount(self, ir: IR, n: int) -> NDArray[np.int_]:
        refcount = np.zeros((n, n), dtype=int)
        for statement in getattr(ir, "statements", []):
            if isinstance(statement, Instruction):
                args = statement.arguments
                if args and len(args) > 1 and all(isinstance(arg, Qubit) for arg in args):
                    qubit_args = [arg for arg in args if isinstance(arg, Qubit)]
                    for q_0, q_1 in zip(qubit_args[:-1], qubit_args[1:]):
                        refcount[q_0.index, q_1.index] += 1
                        refcount[q_1.index, q_0.index] += 1
        return refcount

    def build_cost_matrix(self, refcount: NDArray[np.int_], distance: NDArray[np.int_], n: int) -> NDArray[np.int_]:
        cost_matrix = np.zeros((n, n), dtype=int)
        for i in range(n):
            for k in range(n):
                cost_matrix[i, k] = sum(refcount[i, j] * distance[k, m] for j in range(n) for m in range(n))
        return cost_matrix

    def build_constraints(self, n: int) -> tuple[list[LinearConstraint], NDArray[np.bool_], Bounds]:
        num_vars = n * n
        eq_a = np.zeros((n, num_vars))
        for q_i in range(n):
            for q_k in range(n):
                eq_a[q_i, q_i * n + q_k] = 1
        eq_b = np.ones(n)

        ub_a = np.zeros((n, num_vars))
        for q_k in range(n):
            for q_i in range(n):
                ub_a[q_k, q_i * n + q_k] = 1
        ub_b = np.ones(n)
        integrality = np.ones(num_vars, dtype=bool)
        bounds = Bounds(0, 1)
        constraints = [LinearConstraint(eq_a, eq_b, eq_b), LinearConstraint(ub_a, -np.inf, ub_b)]
        return constraints, integrality, bounds

    def build_milp_options(self) -> dict[str, float]:
        milp_options = {}
        if self.timeout is not None:
            milp_options["time_limit"] = self.timeout
        return milp_options

    def solve_and_extract_mapping(
        self,
        cost_matrix: NDArray[np.int_],
        constraints: list[LinearConstraint],
        integrality: NDArray[np.bool_],
        bounds: Bounds,
        milp_options: dict[str, float],
        n: int,
    ) -> list[int]:
        cost = cost_matrix.flatten()
        res = milp(c=cost, constraints=constraints, integrality=integrality, bounds=bounds, options=milp_options)
        if not res.success:
            error_message = (
                f"MIP solver failed to find a feasible mapping. Status: {res.status}, Message: {res.message}"
            )
            raise RuntimeError(error_message)
        x_sol = res.x.reshape((n, n))
        mapping = []
        for q_i in range(n):
            k = int(np.argmax(x_sol[q_i]))
            mapping.append(k)
        return mapping
