# OpenQL MIP-Like Mapper
from __future__ import annotations

from typing import Any, Optional

import numpy as np
from numpy.typing import NDArray
from scipy.optimize import Bounds, LinearConstraint, milp

from opensquirrel.ir import IR, Instruction, Qubit
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping


def compute_distance_matrix(connectivity: dict[str, list[int]], n: int) -> NDArray[np.int_]:
    dist = np.full((n, n), np.inf)
    np.fill_diagonal(dist, 0)
    for i_str, neighbors in connectivity.items():
        i = int(i_str)
        for j in neighbors:
            dist[i, j] = 1
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i, j] > dist[i, k] + dist[k, j]:
                    dist[i, j] = dist[i, k] + dist[k, j]
    dist[dist == np.inf] = 999999
    return dist.astype(int)


class MIPMapper(Mapper):
    def __init__(
        self,
        qubit_register_size: int,
        connectivity: dict[str, list[int]],
        timeout: Optional[float] = None,  # noqa: UP045
        **kwargs: Any,
    ) -> None:
        self.qubit_register_size = qubit_register_size
        self.connectivity = connectivity
        self.timeout = timeout
        self.distance_matrix = compute_distance_matrix(connectivity, qubit_register_size)
        super().__init__(qubit_register_size, None, **kwargs)

    def map(self, ir: IR) -> Mapping:  # noqa: C901
        """
        Find an initial mapping of virtual qubits to physical qubits that minimizes
        the sum of distances between mapped operands of all two-qubit gates, using
        Mixed Integer Programming (MIP).

        This method formulates the mapping as a linear assignment problem, where the
        objective is to minimize the total "distance cost" of executing all two-qubit
        gates, given the hardware connectivity.

        Args:
            ir (IR): The intermediate representation of the quantum circuit to be mapped.

        Returns:
            Mapping: An object representing the mapping from virtual to physical qubits.

        Raises:
            RuntimeError: If the MIP solver fails to find a feasible mapping or times out.
            RuntimeError: If the number of virtual qubits exceeds the number of physical qubits.
        """
        n = self.qubit_register_size
        distance = self.distance_matrix

        # Check if the number of virtual qubits exceeds the number of physical qubits
        max_virtual_index = max(
            (
                q.index
                for stmt in getattr(ir, "statements", [])
                if isinstance(stmt, Instruction)
                for q in getattr(stmt, "arguments", [])
                if isinstance(q, Qubit)
            ),
            default=-1,
        )
        if max_virtual_index >= n:
            error_message = (
                f"Number of virtual qubits ({max_virtual_index + 1}) exceeds number of physical qubits ({n})"
            )
            raise RuntimeError(error_message)

        # Build refcount matrix
        refcount = np.zeros((n, n), dtype=int)
        for statement in getattr(ir, "statements", []):
            if not isinstance(statement, Instruction):
                continue
            args = statement.arguments
            if args and len(args) > 1 and all(isinstance(arg, Qubit) for arg in args):
                qubit_args = [arg for arg in args if isinstance(arg, Qubit)]
                qubit_index_pairs = [(q0.index, q1.index) for q0, q1 in zip(qubit_args[:-1], qubit_args[1:])]
                for i, j in qubit_index_pairs:
                    refcount[i, j] += 1
                    refcount[j, i] += 1

        num_vars = n * n

        cost_matrix = np.zeros((n, n))
        for i in range(n):
            for k in range(n):
                cost_matrix[i, k] = sum(refcount[i, j] * distance[k, m] for j in range(n) for m in range(n))

        c = cost_matrix.flatten()

        # Constraints:

        # 1. Each virtual qubit assigned to exactly one real qubit
        a_eq1 = np.zeros((n, num_vars))
        for i in range(n):
            for k in range(n):
                a_eq1[i, i * n + k] = 1
        b_eq1 = np.ones(n)

        # 2. Each real qubit assigned at most one virtual qubit
        a_ub = np.zeros((n, num_vars))
        for k in range(n):
            for i in range(n):
                a_ub[k, i * n + k] = 1
        b_ub = np.ones(n)

        integrality = np.ones(num_vars, dtype=bool)
        bounds = Bounds(0, 1)

        constraints = [LinearConstraint(a_eq1, b_eq1, b_eq1), LinearConstraint(a_ub, -np.inf, b_ub)]

        time_limit = self.timeout
        milp_options = {}
        if time_limit is not None:
            milp_options["time_limit"] = time_limit

        res = milp(c=c, constraints=constraints, integrality=integrality, bounds=bounds, options=milp_options)

        if not res.success:
            error_message = f"MIP solver failed: {res.message}"
            raise RuntimeError(error_message)

        x_sol = res.x.reshape((n, n))
        mapping = []
        for i in range(n):
            k = int(np.argmax(x_sol[i]))
            mapping.append(k)

        return Mapping(mapping)
