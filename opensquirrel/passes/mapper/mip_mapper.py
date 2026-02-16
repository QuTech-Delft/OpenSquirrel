# OpenQL MIP-Like Mapper. This mapper pass is based on:
# https://github.com/QuTech-Delft/OpenQL/blob/develop/src/ql/pass/map/qubits/place_mip/place_mip.cc

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp

from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.passes.mapper.general_mapper import Mapper
from opensquirrel.passes.mapper.mapping import Mapping

if TYPE_CHECKING:
    from opensquirrel import Connectivity
    from opensquirrel.ir import IR

DISTANCE_UL = 999999


class MIPMapper(Mapper):
    """
    Mixed Integer Programming (MIP) mapper for finding optimal initial qubit mappings.

    This mapper finds an initial mapping of virtual qubits to physical qubits that minimizes
    the sum of distances between mapped operands of all two-qubit gates, using a linearized
    MIP formulation based on OpenQL's approach.

    The formulation uses binary variables x[i][k] indicating whether virtual qubit i
    is mapped to physical qubit k, and continuous variables w[i][k] representing the
    cost contribution for mapping i to k.

    The objective function minimizes sum(w[i][k]) + epsilon * sum_{i,k: i!=k} x[i][k],
    where the epsilon term provides a small penalty for non-identity mappings as a tiebreaker.

    Subject to the following constraints:
    1. Each virtual qubit assigned to exactly one physical qubit: sum_k x[i][k] == 1
    2. Each physical qubit assigned to at most one virtual qubit: sum_i x[i][k] <= 1
    3. Linearization: costmax[i][k] * x[i][k] + sum_{j,l} refcount[i][j]*distance[k][l]*x[j][l] - w[i][k] <= costmax[i][k]

    Args:
        connectivity: Physical qubit connectivity graph.
        timeout: Maximum time (in seconds) allowed for the MIP solver. None means no timeout.
        epsilon: Small penalty coefficient for non-identity mappings (default: 1e-6).

    Example:
        >>> connectivity = {"0": [1], "1": [0, 2], "2": [1]}
        >>> mapper = MIPMapper(connectivity=connectivity, timeout=10.0)
        >>> mapping = mapper.map(circuit, qubit_register_size=3)
    """  # noqa: E501

    def __init__(
        self,
        connectivity: Connectivity,
        timeout: float | None = None,
        epsilon: float = 1e-6,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.connectivity = connectivity
        self.timeout = timeout
        self.epsilon = epsilon
        self.num_virtual_qubits = 0
        self.num_physical_qubits = 0
        self.num_x_vars = 0
        self.num_w_vars = 0
        self.num_vars = 0

    def map(
        self,
        ir: IR,
        qubit_register_size: int,
        interaction_graph: dict[tuple[int, int], int] | None = None,
    ) -> Mapping:
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
            interaction_graph: Pre-computed interaction graph (not used by this mapper).

        Returns:
            Mapping: Mapping from virtual to physical qubits.

        Raises:
            RuntimeError: If the MIP solver fails to find a feasible mapping or times out.
            RuntimeError: If the number of virtual qubits exceeds the number of physical qubits.
        """
        if interaction_graph is not None:
            msg = (
                "The MIPMapper does not effectively use the interaction graph, thus this argument should be set to None"
            )
            warnings.warn(msg, stacklevel=2)
        self.num_virtual_qubits = qubit_register_size
        self.num_physical_qubits = len(self.connectivity)
        self.num_x_vars = self.num_virtual_qubits * self.num_physical_qubits
        self.num_w_vars = self.num_virtual_qubits * self.num_physical_qubits
        self.num_vars = self.num_x_vars + self.num_w_vars

        if self.num_virtual_qubits > self.num_physical_qubits:
            error_message = (
                f"Number of virtual qubits ({self.num_virtual_qubits}) exceeds "
                f"number of physical qubits ({self.num_physical_qubits})"
            )
            raise RuntimeError(error_message)

        distance = self._get_distance()
        reference_counter = self._get_reference_counter(ir, self.num_virtual_qubits)

        cost, constraints, integrality, bounds = self._get_linearized_formulation(reference_counter, distance)

        milp_options = self._get_milp_options()
        mapping = self._solve_and_extract_mapping(cost, constraints, integrality, bounds, milp_options)
        return Mapping(mapping)

    def _get_distance(self) -> list[list[int]]:
        distance = np.full((self.num_physical_qubits, self.num_physical_qubits), DISTANCE_UL, dtype=int)
        np.fill_diagonal(distance, 0)

        for start_qubit_index, end_qubit_indices in self.connectivity.items():
            for end_qubit_index in end_qubit_indices:
                distance[int(start_qubit_index), end_qubit_index] = 1

        for k in range(self.num_physical_qubits):
            for i in range(self.num_physical_qubits):
                for j in range(self.num_physical_qubits):
                    if distance[i][j] > distance[i][k] + distance[k][j]:
                        distance[i][j] = distance[i][k] + distance[k][j]

        return list(distance)

    @staticmethod
    def _get_reference_counter(ir: IR, num_virtual_qubits: int) -> list[list[int]]:
        reference_counter = [[0 for _ in range(num_virtual_qubits)] for _ in range(num_virtual_qubits)]
        for statement in ir.statements:
            if isinstance(statement, TwoQubitGate):
                qubit_operands = statement.qubit_operands
                if len(qubit_operands) == 2:
                    q_0, q_1 = qubit_operands[0], qubit_operands[1]
                    reference_counter[q_0.index][q_1.index] += 1
                    reference_counter[q_1.index][q_0.index] += 1
        return reference_counter

    def _get_linearized_formulation(
        self,
        reference_counter: list[list[int]],
        distance: list[list[int]],
    ) -> tuple[list[float], list[LinearConstraint], list[int], Bounds]:
        """
        Create the linearized MIP formulation.

        Args:
            reference_counter: Matrix counting two-qubit gate interactions between virtual qubits.
            distance: Distance matrix between physical qubits (minimum swap count).

        Returns:
            Tuple of (cost coefficients, constraints, integrality indicators, variable bounds).
        """
        max_cost = self._compute_max_cost(reference_counter, distance)
        cost = self._get_cost()
        constraints = self._get_constraints(reference_counter, distance, max_cost)
        integrality, bounds = self._get_integrality_and_bounds()

        return cost, constraints, integrality, bounds

    def _compute_max_cost(
        self,
        reference_counter: list[list[int]],
        distance: list[list[int]],
    ) -> np.ndarray:
        max_cost = np.zeros((self.num_virtual_qubits, self.num_physical_qubits))
        for i in range(self.num_virtual_qubits):
            for k in range(self.num_physical_qubits):
                max_cost[i][k] = sum(
                    reference_counter[i][j] * distance[k][l]
                    for j in range(self.num_virtual_qubits)
                    for l in range(self.num_physical_qubits)  # noqa: E741
                )
        return max_cost

    def _get_cost(self) -> list[float]:
        x_cost = [0.0] * self.num_x_vars
        for i in range(self.num_virtual_qubits):
            for k in range(self.num_physical_qubits):
                if i != k:
                    x_cost[i * self.num_physical_qubits + k] += self.epsilon
                x_cost[i * self.num_physical_qubits + k] += self.epsilon * self.epsilon * k

        w_cost = [1.0] * self.num_w_vars
        return x_cost + w_cost

    def _get_constraints(
        self,
        reference_counter: list[list[int]],
        distance: list[list[int]],
        max_cost: np.ndarray,
    ) -> list[LinearConstraint]:
        eq_a = np.zeros((self.num_virtual_qubits, self.num_vars))
        for q_i in range(self.num_virtual_qubits):
            for q_k in range(self.num_physical_qubits):
                eq_a[q_i, q_i * self.num_physical_qubits + q_k] = 1
        eq_b = np.ones(self.num_virtual_qubits)

        ub_a = np.zeros((self.num_physical_qubits, self.num_vars))
        for q_k in range(self.num_physical_qubits):
            for q_i in range(self.num_virtual_qubits):
                ub_a[q_k, q_i * self.num_physical_qubits + q_k] = 1
        ub_b = np.ones(self.num_physical_qubits)

        num_linearization_constraints = self.num_virtual_qubits * self.num_physical_qubits
        lin_a = np.zeros((num_linearization_constraints, self.num_vars))
        lin_b = np.zeros(num_linearization_constraints)

        constraint_idx = 0
        for i in range(self.num_virtual_qubits):
            for k in range(self.num_physical_qubits):
                lin_a[constraint_idx, i * self.num_physical_qubits + k] = max_cost[i][k]

                for j in range(self.num_virtual_qubits):
                    for l in range(self.num_physical_qubits):  # noqa: E741
                        lin_a[constraint_idx, j * self.num_physical_qubits + l] += (
                            reference_counter[i][j] * distance[k][l]
                        )

                lin_a[constraint_idx, self.num_x_vars + i * self.num_physical_qubits + k] = -1
                lin_b[constraint_idx] = max_cost[i][k]
                constraint_idx += 1

        return [
            LinearConstraint(eq_a, eq_b, eq_b),
            LinearConstraint(ub_a, -np.inf, ub_b),
            LinearConstraint(lin_a, -np.inf, lin_b),
        ]

    def _get_integrality_and_bounds(self) -> tuple[list[int], Bounds]:
        integrality = [1] * self.num_x_vars + [0] * self.num_w_vars
        lb = np.concatenate([np.zeros(self.num_x_vars), np.zeros(self.num_w_vars)])
        ub = np.concatenate([np.ones(self.num_x_vars), np.full(self.num_w_vars, np.inf)])
        bounds = Bounds(lb, ub)
        return integrality, bounds

    def _get_milp_options(self) -> dict[str, float]:
        milp_options = {}
        if self.timeout is not None:
            milp_options["time_limit"] = self.timeout
        return milp_options

    def _solve_and_extract_mapping(
        self,
        cost: list[float],
        constraints: list[LinearConstraint],
        integrality: list[int],
        bounds: Bounds,
        milp_options: dict[str, float],
    ) -> list[int]:
        res = milp(c=cost, constraints=constraints, integrality=integrality, bounds=bounds, options=milp_options)

        if not res.success:
            error_message = (
                f"MIP solver failed to find a feasible mapping. Status: {res.status}, Message: {res.message}"
            )
            raise RuntimeError(error_message)

        x_sol = res.x[: self.num_x_vars].reshape((self.num_virtual_qubits, self.num_physical_qubits))

        return [int(np.argmax(x)) for x in x_sol]
