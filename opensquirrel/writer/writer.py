from opensquirrel.circuit import Circuit
from opensquirrel.ir import (Bit, Comment, Float, Gate, Int, IRVisitor,
                             Measure, Qubit)
from opensquirrel.register_manager import RegisterManager


class _WriterImpl(IRVisitor):
    number_of_significant_digits = 8

    def __init__(self, register_manager: RegisterManager) -> None:
        self.register_manager = register_manager
        qubit_register_size = self.register_manager.get_qubit_register_size()
        qubit_register_name = self.register_manager.get_qubit_register_name()
        bit_register_size = self.register_manager.get_bit_register_size()
        bit_register_name = self.register_manager.get_bit_register_name()
        self.output = "version 3.0\n\n{}\n{}\n".format(
            f"qubit[{qubit_register_size}] {qubit_register_name}",
            f"bit[{bit_register_size}] {bit_register_name}\n" if bit_register_size > 0 else "",
        )

    def visit_bit(self, bit: Bit) -> str:
        bit_register_name = self.register_manager.get_bit_register_name()
        return f"{bit_register_name}[{bit.index}]"

    def visit_qubit(self, qubit: Qubit) -> str:
        qubit_register_name = self.register_manager.get_qubit_register_name()
        return f"{qubit_register_name}[{qubit.index}]"

    def visit_int(self, i: Int) -> str:
        return f"{i.value}"

    def visit_float(self, f: Float) -> str:
        return f"{f.value:.{self.number_of_significant_digits}}"

    def visit_measure(self, measure: Measure) -> None:
        if measure.is_abstract:
            self.output += f"{measure.name}\n"
            return
        bit_argument = measure.arguments[1].accept(self)  # type: ignore[index]
        qubit_argument = measure.arguments[0].accept(self)  # type: ignore[index]
        self.output += f"{bit_argument} = {measure.name} {qubit_argument}\n"

    def visit_gate(self, gate: Gate) -> None:
        gate_name = gate.name
        if gate.is_anonymous:
            if "MatrixGate" in gate_name:
                # In the case of a MatrixGate the newlines should be removed from the array
                # such that the array is printed on a single line.
                gate_name = gate_name.replace("\n", "")
            self.output += f"{gate_name}\n"
            return
        if any(not isinstance(arg, Qubit) for arg in gate.arguments):  # type: ignore[union-attr]
            params = [arg.accept(self) for arg in gate.arguments if not isinstance(arg, Qubit)]  # type: ignore[union-attr]
            gate_name += f"({', '.join(params)})"
        qubit_args = (arg.accept(self) for arg in gate.arguments if isinstance(arg, Qubit))  # type: ignore[union-attr]
        self.output += f"{gate_name} {', '.join(qubit_args)}\n"

    def visit_comment(self, comment: Comment) -> None:
        self.output += f"\n/* {comment.str} */\n\n"


def circuit_to_string(circuit: Circuit) -> str:
    writer_impl = _WriterImpl(circuit.register_manager)

    circuit.ir.accept(writer_impl)

    return writer_impl.output
