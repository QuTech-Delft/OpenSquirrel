from opensquirrel.passes.merger.general_merger import Merger
from opensquirrel.ir import IR, Instruction, Gate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.circuit import Circuit
from opensquirrel.register_manager import RegisterManager, QubitRegister, BitRegister
from typing import cast

import numpy as np
from copy import copy
from collections import OrderedDict
from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from functools import reduce
from opensquirrel.ir.semantics.matrix_gate import MatrixGateSemantic

from opensquirrel.circuit_builder import CircuitBuilder

def group_gates(gates: list[list[int]]) -> list[tuple[tuple[int, int], list[int]]]:
    groups = []
    group = set()
    statement_indices = []
    for i, qubit_indices in enumerate(gates):
        
        # Reset group if current statement is not a Gate
        if not qubit_indices:
            if group:
                groups.append((tuple(group), copy(statement_indices)))
            group.clear()
            statement_indices.clear()
            continue

        # If the group has more than 2 qubits, it means that we have encountered a new group of gates. 
        if len(group | set(qubit_indices)) > 2:
            if group:                
                groups.append((tuple(group), copy(statement_indices)))
            group = set(qubit_indices)
            statement_indices.clear()
        
        group.update(qubit_indices)
        statement_indices.append(i)

    if group:
        groups.append((tuple(group), copy(statement_indices)))
    return groups


class TwoQubitGatesMerger(Merger):
    def merge(self, ir: IR, qubit_register_size: int) -> None:
        """Merge all consecutive two-qubit gates in the circuit.

        Args:
            ir (IR): Intermediate representation of the circuit.
            qubit_register_size (int): Size of the qubit register

        """

        gates = [statement.qubit_indices if isinstance(statement, Gate) else [] for statement in ir.statements]
        groups = group_gates(gates)
        
        new_gates = []
            
        for qubit_indices, statement_indices in groups:  
            if len(statement_indices) == 1:
                new_gates.append(ir.statements[statement_indices[0]])
                continue

            sub_circuit_matrix = np.eye(1 << len(qubit_indices), dtype=np.complex128)            

            qubit0, qubit1 = qubit_indices
            for statement_index in statement_indices:
                gate = cast("Gate", ir.statements[statement_index])
                if isinstance(gate, TwoQubitGate):
                    sub_circuit_matrix = sub_circuit_matrix @ gate.matrix
                
                if isinstance(gate, SingleQubitGate):
                    if gate.qubit == qubit0:
                        sub_circuit_matrix =  sub_circuit_matrix @ np.kron(gate.matrix, np.eye(2, dtype=np.complex128))
                    if gate.qubit == qubit1:
                        sub_circuit_matrix = sub_circuit_matrix @ np.kron(np.eye(2, dtype=np.complex128), gate.matrix)

            
            gate = TwoQubitGate(*qubit_indices, gate_semantic=MatrixGateSemantic(sub_circuit_matrix))
            new_gates.append(gate)

        # Replace the original statements with the merged gates
        new_statements = []
        current_index = 0
        for new_gate, (_, statement_indices) in zip(new_gates, groups, strict=True):
            
            if current_index < statement_indices[0]:
                new_statements.extend(ir.statements[current_index:statement_indices[0]])
            
            new_statements.append(new_gate)
            current_index = statement_indices[-1] + 1

        # Replace the original statements with the merged gates
        ir.statements = new_statements



            