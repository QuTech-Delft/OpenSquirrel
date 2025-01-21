from typing import cast

from opensquirrel.ir import IR, Instruction, Qubit
from opensquirrel.passes.router.general_router import Router


class RoutingChecker(Router):
    def __init__(self, connectivity: dict[str, list[int]]) -> None:
        self.connectivity = connectivity

    def route(self, ir: IR) -> None:
        non_executable_interactions = []
        for statement in ir.statements:
            instruction: Instruction = cast(Instruction, statement)
            args = instruction.arguments
            if args and len(args) > 1 and all(isinstance(arg, Qubit) for arg in args):
                qubit_args = [arg for arg in args if isinstance(arg, Qubit)]
                qubit_index_pairs = [(q0.index, q1.index) for q0, q1 in zip(qubit_args[:-1], qubit_args[1:])]
                for i, j in qubit_index_pairs:
                    if j not in self.connectivity.get(str(i), []):
                        non_executable_interactions.append((i, j))

        if non_executable_interactions:
            error_message = (
                f"The following qubit interactions in the circuit prevent a 1-to-1 mapping:"
                f"{set(non_executable_interactions)}"
            )
            raise ValueError(error_message)
