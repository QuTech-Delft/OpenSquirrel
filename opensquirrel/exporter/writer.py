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

    def visit_measure(self, measure: Measure):
        self.output += f"{measure.name} {measure.arguments[0].accept(self)}\n"

    def visit_gate(self, gate: Gate):
        if gate.is_anonymous:
            self.output += "<anonymous-gate>\n"
            return

        gate_name = gate.name
        if any(not isinstance(arg, Qubit) for arg in gate.arguments):
            params = [arg.accept(self) for arg in gate.arguments if not isinstance(arg, Qubit)]
            gate_name += f"({', '.join(params)})"
        qubit_args = (arg.accept(self) for arg in gate.arguments if isinstance(arg, Qubit))
        self.output += f"{gate_name} {', '.join(qubit_args)}\n"

    def visit_comment(self, comment: Comment):
        self.output += f"\n/* {comment.str} */\n\n"


def squirrel_ir_to_string(squirrel_ir: SquirrelIR):
    writer_impl = _WriterImpl(squirrel_ir.number_of_qubits, squirrel_ir.qubit_register_name)

    squirrel_ir.accept(writer_impl)

    return writer_impl.output
