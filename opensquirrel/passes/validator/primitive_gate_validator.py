from typing import Any

from opensquirrel.ir import IR, Instruction
from opensquirrel.passes.validator.general_validator import Validator


class PrimitiveGateValidator(Validator):
    def __init__(self, primitive_gate_set: list[str], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.primitive_gate_set = primitive_gate_set

    def validate(self, ir: IR) -> None:
        """
        Check if all unitary gates in the circuit are part of the primitive gate set.

        Args:
            ir (IR): The intermediate representation of the circuit to be checked.

        Raises:
            ValueError: If any unitary gate in the circuit is not part of the primitive gate set.
        """
        gates_not_in_primitive_gate_set = [
            statement.name
            for statement in ir.statements
            if isinstance(statement, Instruction) and statement.name not in self.primitive_gate_set
        ]
        if gates_not_in_primitive_gate_set:
            unsupported_gates = list(set(gates_not_in_primitive_gate_set))
            error_message = "the following gates are not in the primitive gate set: " + ", ".join(unsupported_gates)
            raise ValueError(error_message)
