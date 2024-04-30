from opensquirrel.squirrel_ir import Comment, Float, Gate, Int, Measure, Qubit, SquirrelIR, SquirrelIRVisitor


class _WriterImpl(SquirrelIRVisitor):
    number_of_significant_digits = 8

    def __init__(self, number_of_qubits: int, qubit_register_name: str) -> None:
        self.qubit_register_name = qubit_register_name
        self.output = f"""version 3.0\n\nqubit[{number_of_qubits}] {qubit_register_name}\n\n"""

    def visit_qubit(self, qubit: Qubit) -> str:
        return f"{self.qubit_register_name}[{qubit.index}]"

    def visit_int(self, i: Int) -> str:
        return f"{i.value}"

    def visit_float(self, f: Float) -> str:
        return f"{f.value:.{self.number_of_significant_digits}}"

    def visit_measure(self, measure: Measure) -> None:
        self.output += f"{measure.name} {measure.arguments[0].accept(self)}\n"

    def visit_gate(self, gate: Gate) -> None:
        if gate.is_anonymous:
            self.output += "<anonymous-gate>\n"
            return

        formatted_args = (arg.accept(self) for arg in gate.arguments)
        self.output += f"{gate.name} {', '.join(formatted_args)}\n"

    def visit_comment(self, comment: Comment) -> None:
        self.output += f"\n/* {comment.str} */\n\n"


def squirrel_ir_to_string(squirrel_ir: SquirrelIR) -> str:
    writer_impl = _WriterImpl(squirrel_ir.number_of_qubits, squirrel_ir.qubit_register_name)

    squirrel_ir.accept(writer_impl)

    return writer_impl.output
