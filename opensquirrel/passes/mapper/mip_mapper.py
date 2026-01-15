# OpenQL MIP-Like Mapper. This mapper pass takes inspiration from: 
# https://github.com/QuTech-Delft/OpenQL/blob/develop/src/ql/pass/map/qubits/place_mip/place_mip.cc

from __future__ import annotations

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
    def __init__(
        self,
        connectivity: Connectivity,
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
        reference_counter = self._get_reference_counter(ir, qubit_register_size)
        
        cost, constraints, integrality, bounds = self._get_linearized_formulation(
            reference_counter, distance, qubit_register_size, num_physical_qubits
        )
        
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

    def _get_reference_counter(self, ir: IR, num_virtual_qubits: int) -> list[list[int]]:
        reference_counter = [[0 for _ in range(num_virtual_qubits)] for _ in range(num_virtual_qubits)]
        for statement in getattr(ir, "statements", []):
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
        num_virtual_qubits: int,
        num_physical_qubits: int,
    ) -> tuple[list[float], list[LinearConstraint], list[bool], Bounds]:
        """
        Create the linearized MIP formulation following OpenQL's approach.
        
        Variables:
            x[i][k]: binary, virtual qubit i mapped to physical qubit k (num_virtual * num_physical)
            w[i][k]: continuous, cost contribution for mapping i to k (num_virtual * num_physical)
        
        Objective:
            min sum(w[i][k]) + epsilon * sum_{i,k: i!=k} x[i][k]
            (small epsilon penalty for non-identity mappings as tiebreaker)
        
        Constraints:
            1. Each virtual qubit assigned to exactly one physical qubit: sum_k x[i][k] == 1
            2. Each physical qubit assigned to at most one virtual qubit: sum_i x[i][k] <= 1
            3. Linearization: costmax[i][k] * x[i][k] + sum_{j,l} refcount[i][j]*distance[k][l]*x[j][l] - w[i][k] <= costmax[i][k]
        """
        num_x_vars = num_virtual_qubits * num_physical_qubits
        num_w_vars = num_virtual_qubits * num_physical_qubits
        num_vars = num_x_vars + num_w_vars
    
        costmax = np.zeros((num_virtual_qubits, num_physical_qubits))
        for i in range(num_virtual_qubits):
            for k in range(num_physical_qubits):
                costmax[i][k] = sum(
                    reference_counter[i][j] * distance[k][l]
                    for j in range(num_virtual_qubits)
                    for l in range(num_physical_qubits)
                )
        
        epsilon = 1e-6  
        x_cost = np.zeros(num_x_vars)
        for i in range(num_virtual_qubits):
            for k in range(num_physical_qubits):
                if i != k:
                    x_cost[i * num_physical_qubits + k] += epsilon
                x_cost[i * num_physical_qubits + k] += epsilon * epsilon * k
        
        cost = np.concatenate([x_cost, np.ones(num_w_vars)])

        eq_a = np.zeros((num_virtual_qubits, num_vars))
        for i in range(num_virtual_qubits):
            for k in range(num_physical_qubits):
                eq_a[i, i * num_physical_qubits + k] = 1
        eq_b = np.ones(num_virtual_qubits)
        
        ub_a = np.zeros((num_physical_qubits, num_vars))
        for k in range(num_physical_qubits):
            for i in range(num_virtual_qubits):
                ub_a[k, i * num_physical_qubits + k] = 1
        ub_b = np.ones(num_physical_qubits)
        
        num_linearization_constraints = num_virtual_qubits * num_physical_qubits
        lin_a = np.zeros((num_linearization_constraints, num_vars))
        lin_b = np.zeros(num_linearization_constraints)
        
        constraint_idx = 0
        for i in range(num_virtual_qubits):
            for k in range(num_physical_qubits):
                lin_a[constraint_idx, i * num_physical_qubits + k] = costmax[i][k]
                
                for j in range(num_virtual_qubits):
                    for l in range(num_physical_qubits):
                        lin_a[constraint_idx, j * num_physical_qubits + l] += (
                            reference_counter[i][j] * distance[k][l]
                        )
                
                lin_a[constraint_idx, num_x_vars + i * num_physical_qubits + k] = -1
                
                lin_b[constraint_idx] = costmax[i][k]
                
                constraint_idx += 1
        
        constraints = [
            LinearConstraint(eq_a, eq_b, eq_b), 
            LinearConstraint(ub_a, -np.inf, ub_b),  
            LinearConstraint(lin_a, -np.inf, lin_b),  
        ]
        
        integrality = np.concatenate([np.ones(num_x_vars, dtype=bool), np.zeros(num_w_vars, dtype=bool)])
        
        lb = np.concatenate([np.zeros(num_x_vars), np.zeros(num_w_vars)])
        ub = np.concatenate([np.ones(num_x_vars), np.full(num_w_vars, np.inf)])
        bounds = Bounds(lb, ub)
        
        return list(cost), constraints, list(integrality), bounds

    def _get_milp_options(self) -> dict[str, float]:
        milp_options = {}
        if self.timeout is not None:
            milp_options["time_limit"] = self.timeout
        return milp_options

    def _solve_and_extract_mapping(
        self,
        cost: list[float],
        constraints: list[LinearConstraint],
        integrality: list[bool],
        bounds: Bounds,
        milp_options: dict[str, float],
        num_virtual_qubits: int,
        num_physical_qubits: int,
    ) -> list[int]:
        res = milp(c=cost, constraints=constraints, integrality=integrality, bounds=bounds, options=milp_options)

        if not res.success:
            error_message = (
                f"MIP solver failed to find a feasible mapping. Status: {res.status}, Message: {res.message}"
            )
            raise RuntimeError(error_message)

        num_x_vars = num_virtual_qubits * num_physical_qubits
        x_sol = res.x[:num_x_vars].reshape((num_virtual_qubits, num_physical_qubits))
        
        mapping = []
        for i in range(num_virtual_qubits):
            k = int(np.argmax(x_sol[i]))
            mapping.append(k)

        return mapping

