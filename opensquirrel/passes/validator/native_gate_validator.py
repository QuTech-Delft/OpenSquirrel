from opensquirrel.ir import IR, Unitary
from opensquirrel.passes.validator import Validator


class NativeGateValidator(Validator):
    def __init__(self, native_gate_set: list[str]) -> None:
        self.native_gate_set = native_gate_set

    def validate(self, ir: IR) -> None:
        """
        Check if all unitary gates in the circuit are part of the native gate set.

        Args:
            ir (IR): The intermediate representation of the circuit to be checked.

        Raises:
            ValueError: If any unitary gate in the circuit is not part of the native gate set.
        """
        gates_not_in_native_gate_set = [
            statement.name
            for statement in ir.statements
            if isinstance(statement, Unitary) and statement.name not in self.native_gate_set
        ]
        if gates_not_in_native_gate_set:
            error_message = f"the following gates are not in the native gate set: {set(gates_not_in_native_gate_set)}"
            raise ValueError(error_message)
