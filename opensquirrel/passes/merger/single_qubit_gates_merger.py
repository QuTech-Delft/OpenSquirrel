from typing import cast

from opensquirrel import I
from opensquirrel.ir import IR, AsmDeclaration, Barrier, Instruction, Qubit
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.passes.merger.general_merger import Merger, compose_bloch_sphere_rotations


class SingleQubitGatesMerger(Merger):
    def merge(self, ir: IR, qubit_register_size: int) -> None:
        """Merge all consecutive 1-qubit gates in the circuit.
        Gates obtained from merging other gates become anonymous gates.

        Args:
            ir: Intermediate representation of the circuit.
            qubit_register_size: Size of the qubit register

        """
        accumulators_per_qubit: dict[Qubit, BlochSphereRotation] = {
            Qubit(qubit_index): I(qubit_index) for qubit_index in range(qubit_register_size)
        }

        statement_index = 0
        while statement_index < len(ir.statements):
            statement = ir.statements[statement_index]

            # Accumulate consecutive Bloch sphere rotations
            instruction: Instruction = cast("Instruction", statement)
            if isinstance(instruction, BlochSphereRotation):
                already_accumulated = accumulators_per_qubit[instruction.qubit]
                composed = compose_bloch_sphere_rotations(already_accumulated, instruction)
                accumulators_per_qubit[instruction.qubit] = composed
                del ir.statements[statement_index]
                continue

            def insert_accumulated_bloch_sphere_rotations(qubits: list[Qubit]) -> None:
                nonlocal statement_index
                for qubit in qubits:
                    if not accumulators_per_qubit[qubit].is_identity():
                        ir.statements.insert(statement_index, accumulators_per_qubit[qubit])
                        accumulators_per_qubit[qubit] = I(qubit)
                        statement_index += 1

            # For barrier directives, insert all accumulated Bloch sphere rotations
            # For other instructions, insert accumulated Bloch sphere rotations on qubits used by those instructions
            # In any case, reset the dictionary entry for the inserted accumulated Bloch sphere rotations
            if isinstance(instruction, Barrier) or isinstance(statement, AsmDeclaration):
                insert_accumulated_bloch_sphere_rotations([Qubit(i) for i in range(qubit_register_size)])
            else:
                insert_accumulated_bloch_sphere_rotations(instruction.get_qubit_operands())
            statement_index += 1

        for accumulated_bloch_sphere_rotation in accumulators_per_qubit.values():
            if not accumulated_bloch_sphere_rotation.is_identity():
                ir.statements.append(accumulated_bloch_sphere_rotation)
