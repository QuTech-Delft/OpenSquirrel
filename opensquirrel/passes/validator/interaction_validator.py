from typing import Any

from opensquirrel.ir import IR, Instruction, Qubit
from opensquirrel.passes.validator.general_validator import Validator


class InteractionValidator(Validator):
    def __init__(self, connectivity: dict[str, list[int]], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.connectivity = connectivity

    def validate(self, ir: IR) -> None:
        """
        Check if the circuit interactions faciliate a 1-to-1 mapping to the target hardware.

        Args:
            ir (IR): The intermediate representation of the circuit to be checked.

        Raises:
            ValueError: If the circuit can't be mapped to the target hardware.
        """
        non_executable_interactions = []
        for statement in ir.statements:
            if not isinstance(statement, Instruction):
                continue
            args = statement.arguments
            if args and len(args) > 1 and all(isinstance(arg, Qubit) for arg in args):
                qubit_args = [arg for arg in args if isinstance(arg, Qubit)]
                qubit_index_pairs = [(q0.index, q1.index) for q0, q1 in zip(qubit_args[:-1], qubit_args[1:])]
                for i, j in qubit_index_pairs:
                    if j not in self.connectivity.get(str(i), []):
                        non_executable_interactions.append((i, j))

        if non_executable_interactions:
            error_message = (
                f"the following qubit interactions in the circuit prevent a 1-to-1 mapping:"
                f"{set(non_executable_interactions)}"
            )
            raise ValueError(error_message)
