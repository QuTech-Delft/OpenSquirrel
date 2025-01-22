from opensquirrel.ir import IR
from opensquirrel.passes.checker.general_checker import Checker


class NativeGateChecker(Checker):

    def __init__(self, native_gate_set: list[str]) -> None:
        self.native_gate_set = native_gate_set

    def check(self, ir: IR) -> None:
        """
        Check if all gates in the circuit are part of the native gate set.

        Args:
            ir (IR): The intermediate representation of the circuit to be checked.

        Raises:
            ValueError: If any gate in the circuit is not part of the native gate set.
        """
        gates_not_in_native_gate_set = []
        for statement in ir.statements:
            gate = statement.__getattribute__("name")
            if gate not in self.native_gate_set:
                gates_not_in_native_gate_set.append(gate)
        if gates_not_in_native_gate_set:
            error_message = f"The following gates are not in the native gate set: {set(gates_not_in_native_gate_set)}"
            raise ValueError(error_message)
