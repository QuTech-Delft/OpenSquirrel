from opensquirrel.squirrel_ir import Comment, Float, Gate, Int, Measure, Qubit, SquirrelIR, SquirrelIRVisitor


class _WriterImpl(SquirrelIRVisitor):
    number_of_significant_digits = 8

    def __init__(self, number_of_qubits, qubit_register_name):
        self.qubit_register_name = qubit_register_name
        self.output = f"""version 3.0\n\nqubit[{number_of_qubits}] {qubit_register_name}\n\n"""

    def visit_qubit(self, qubit: Qubit):
        return f"{self.qubit_register_name}[{qubit.index}]"

    def visit_int(self, i: Int):
        return f"{i.value}"

    def visit_float(self, f: Float):
        return f"{f.value:.{self.number_of_significant_digits}}"

    def visit_measure(self, measurement: Measure):
        formatted_args = (arg.accept(self) for arg in measurement.arguments)
        self.output += f"{measurement.name} {measurement.arguments[0].accept(self)}\n"

    def visit_gate(self, gate: Gate):
        if gate.is_anonymous:
            self.output += "<anonymous-gate>\n"
            return

        formatted_args = (arg.accept(self) for arg in gate.arguments)
        self.output += f"{gate.name} {', '.join(formatted_args)}\n"

    def visit_comment(self, comment: Comment):
        self.output += f"\n/* {comment.str} */\n\n"


def squirrel_ir_to_string(squirrel_ir: SquirrelIR):
    writer_impl = _WriterImpl(squirrel_ir.number_of_qubits, squirrel_ir.qubit_register_name)

    squirrel_ir.accept(writer_impl)

    return writer_impl.output
