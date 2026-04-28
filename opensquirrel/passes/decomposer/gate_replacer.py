from collections.abc import Callable

from opensquirrel.default_instructions import is_anonymous_gate
from opensquirrel.ir import IR, Gate
from opensquirrel.passes.decomposer.general_decomposer import Decomposer, decompose


class _GenericReplacer(Decomposer):
    def __init__(self, gate_type: type[Gate], replacement_gates_function: Callable[..., list[Gate]]) -> None:
        self.gate_type = gate_type
        self.replacement_gates_function = replacement_gates_function

    def decompose(self, instruction: Gate) -> list[Gate]:
        if is_anonymous_gate(instruction.name) or type(instruction) is not self.gate_type:
            return [instruction]
        return self.replacement_gates_function(*instruction.qubit_operands, *instruction.arguments)


def replace(ir: IR, gate: type[Gate], replacement_gates_function: Callable[..., list[Gate]]) -> None:
    """Replaces all occurrences of a specific gate in the circuit IR with a given sequence of other
    gates.

    Args:
        ir (IR): The circuit IR to modify.
        gate (type[Gate]): Gate to replace.
        replacement_gates_function (Callable[..., list[Gate]]): Function that returns a list of replacement gates.

    """
    generic_replacer = _GenericReplacer(gate, replacement_gates_function)
    decompose(ir, generic_replacer)
