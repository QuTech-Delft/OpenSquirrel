import inspect
from typing import SupportsFloat, SupportsInt

from opensquirrel.circuit import Circuit
from opensquirrel.ir import (
    Bit,
    Float,
    Gate,
    Int,
    IRVisitor,
    NonUnitary,
    Qubit,
    QubitLike,
)
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
        self.output = "version 3.0{}{}{}{}\n\n".format(
            "\n\n" if qubit_register_size > 0 or bit_register_size > 0 else "",
            (f"qubit[{qubit_register_size}] {qubit_register_name}" if qubit_register_size > 0 else ""),
            "\n" if qubit_register_size > 0 and bit_register_size > 0 else "",
            (f"bit[{bit_register_size}] {bit_register_name}" if bit_register_size > 0 else ""),
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

    def visit_float(self, f: SupportsFloat) -> str:
        f = Float(f)
        return f"{f.value:.{self.FLOAT_PRECISION}}"

    def visit_non_unitary(self, non_unitary: NonUnitary) -> None:
        output_instruction = non_unitary.name
        qubit_argument = non_unitary.arguments[0].accept(self)  # type: ignore[index]
        if non_unitary.name == "measure":
            bit_argument = non_unitary.arguments[1].accept(self)  # type: ignore[index]
            output_instruction = f"{bit_argument} = {non_unitary.name}"
        else:
            params = [param.accept(self) for param in non_unitary.arguments[1::]]  # type: ignore[index]
            if params:
                output_instruction = f"{non_unitary.name}({', '.join(params)})"
        self.output += f"{output_instruction} {qubit_argument}\n"

    def visit_gate(self, gate: Gate) -> None:
        gate_name = gate.name
        gate_generator = []
        if gate.generator is not None:
            gate_generator = list(inspect.signature(gate.generator).parameters.keys())
        qubit_function_keys = ["target", "control", "qubit"]
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
                elif gate_generator[pos] in qubit_function_keys and isinstance(arg, QubitLike.__args__):  # type: ignore[attr-defined]
                    qubit_args.append(Qubit(arg).accept(self))

        self.output += f"{gate_name} {', '.join(qubit_args)}\n"


def circuit_to_string(circuit: Circuit) -> str:
    writer_impl = _WriterImpl(circuit.register_manager)
    circuit.ir.accept(writer_impl)

    # Remove all trailing lines and leave only one
    return writer_impl.output.rstrip() + "\n"
