from opensquirrel.circuit import Circuit
from opensquirrel.squirrel_ir import Comment, Float, Gate, Int, Measure, Qubit, SquirrelIRVisitor


class _WriterImpl(SquirrelIRVisitor):
    number_of_significant_digits = 8

    def __init__(self, register_manager):
        self.register_manager = register_manager
        self.output = f"""version 3.0\n\nqubit[{self.register_manager.qubit_register_size}] {self.register_manager.qubit_register_name}\n\n"""

    def visit_qubit(self, qubit: Qubit):
        return f"{self.register_manager.qubit_register_name}[{self.register_manager.get_physical_qubit_index[qubit.index]}]"

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

        formatted_args = (arg.accept(self) for arg in gate.arguments)
        self.output += f"{gate.name} {', '.join(formatted_args)}\n"

    def visit_comment(self, comment: Comment):
        self.output += f"\n/* {comment.str} */\n\n"


def circuit_to_string(circuit: Circuit):
    writer_impl = _WriterImpl(circuit.register_manager)

    circuit.squirrel_ir.accept(writer_impl)

    return writer_impl.output
