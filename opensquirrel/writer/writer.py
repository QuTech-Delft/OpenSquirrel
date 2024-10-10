import inspect
from typing import SupportsInt

from opensquirrel.circuit import Circuit
from opensquirrel.ir import Bit, Comment, Float, Gate, Int, IRVisitor, Measure, Qubit, QubitLike, Reset
from opensquirrel.register_manager import RegisterManager


class _WriterImpl(IRVisitor):
    # Precision used when writing out a float number
    FLOAT_PRECISION = 8

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

    def visit_int(self, i: SupportsInt) -> str:
        i = Int(i)
        return f"{i.value}"

    def visit_float(self, f: Float) -> str:
        return f"{f.value:.{self.FLOAT_PRECISION}}"

    def visit_measure(self, measure: Measure) -> None:
        if measure.is_abstract:
            self.output += f"{measure.name}\n"
            return
        bit_argument = measure.arguments[1].accept(self)  # type: ignore[index]
        qubit_argument = measure.arguments[0].accept(self)  # type: ignore[index]
        self.output += f"{bit_argument} = {measure.name} {qubit_argument}\n"

    def visit_reset(self, reset: Reset) -> None:
        if reset.is_abstract:
            self.output += f"{reset.name}\n"
            return
        qubit_argument = reset.arguments[0].accept(self)  # type: ignore[index]
        self.output += f"{reset.name} {qubit_argument}\n"

    def visit_gate(self, gate: Gate) -> None:
        gate_name = gate.name
        gate_generator = []
        if gate.generator is not None:
            gate_generator = list(inspect.signature(gate.generator).parameters.keys())
        qubit_function_keys = ["target", "control", "q"]
        if gate.is_anonymous:
            if "MatrixGate" in gate_name:
                # In the case of a MatrixGate the newlines should be removed from the array
                # such that the array is printed on a single line.
                gate_name = gate_name.replace("\n", "")
            self.output += f"{gate_name}\n"
            return

        params = []
        qubit_args = []
        if gate.arguments is not None:
            for arg in gate.arguments:
                pos = gate.arguments.index(arg)
                if gate_generator[pos] not in qubit_function_keys:
                    params.append(arg.accept(self))
                    gate_name += f"({', '.join(params)})"
                elif gate_generator[pos] in qubit_function_keys and isinstance(arg, QubitLike.__args__):  # type: ignore
                    qubit_args.append(Qubit(arg).accept(self))

        self.output += f"{gate_name} {', '.join(qubit_args)}\n"

    def visit_comment(self, comment: Comment) -> None:
        self.output += f"\n/* {comment.str} */\n\n"


def circuit_to_string(circuit: Circuit) -> str:
    writer_impl = _WriterImpl(circuit.register_manager)

    circuit.ir.accept(writer_impl)

    return writer_impl.output.rstrip() + "\n"  # remove all trailing lines and leave only one
