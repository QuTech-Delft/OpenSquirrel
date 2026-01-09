from typing import Any, SupportsFloat, SupportsInt

from opensquirrel.circuit import Circuit
from opensquirrel.default_instructions import default_two_qubit_gate_set
from opensquirrel.ir import (
    AsmDeclaration,
    Barrier,
    Bit,
    Float,
    Init,
    Int,
    IRVisitor,
    Measure,
    Qubit,
    Reset,
    String,
    SupportsStr,
    Wait,
)
from opensquirrel.ir.semantics import (
    BsrAngleParam,
    BsrFullParams,
    BsrNoParams,
    BsrUnitaryParams,
)
from opensquirrel.ir.single_qubit_gate import SingleQubitGate, try_match_replace_with_default_gate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.register_manager import RegisterManager


class _WriterImpl(IRVisitor):
    # Precision used when writing out a float number
    FLOAT_PRECISION = 8

    def __init__(self, register_manager: RegisterManager) -> None:
        self.register_manager = register_manager
        qubit_register_size = self.register_manager.qubit_register_size
        qubit_register_name = self.register_manager.qubit_register_name

        bit_register_size = self.register_manager.bit_register_size
        bit_register_name = self.register_manager.bit_register_name
        self.output = "version 3.0{}{}{}{}\n\n".format(
            "\n\n" if qubit_register_size > 0 or bit_register_size > 0 else "",
            (f"qubit[{qubit_register_size}] {qubit_register_name}" if qubit_register_size > 0 else ""),
            "\n" if qubit_register_size > 0 and bit_register_size > 0 else "",
            (f"bit[{bit_register_size}] {bit_register_name}" if bit_register_size > 0 else ""),
        )

    def visit_str(self, s: SupportsStr) -> str:
        s = String(s)
        return f"{s.value}"

    def visit_float(self, f: SupportsFloat) -> str:
        f = Float(f)
        return f"{f.value:.{self.FLOAT_PRECISION}}"

    def visit_int(self, i: SupportsInt) -> str:
        i = Int(i)
        return f"{i.value}"

    def visit_bit(self, bit: Bit) -> str:
        bit_register_name = self.register_manager.bit_register_name
        return f"{bit_register_name}[{bit.index}]"

    def visit_qubit(self, qubit: Qubit) -> str:
        qubit_register_name = self.register_manager.qubit_register_name
        return f"{qubit_register_name}[{qubit.index}]"

    def visit_asm_declaration(self, asm_declaration: AsmDeclaration) -> None:
        backend_name = asm_declaration.backend_name.accept(self)
        backend_code = asm_declaration.backend_code.accept(self)
        self.output += f"asm({backend_name}) '''{backend_code}'''\n"

    def visit_single_qubit_gate(self, gate: SingleQubitGate) -> None:
        if isinstance(gate, SingleQubitGate) and type(gate) is SingleQubitGate:
            gate = try_match_replace_with_default_gate(gate)
        bsr_parameters = gate.bsr.accept(self)
        qubit_operand = gate.qubit.accept(self)
        self.output += f"{gate.name}{bsr_parameters} {qubit_operand}\n"

    def visit_two_qubit_gate(self, gate: TwoQubitGate) -> Any:
        qubit_operand_0 = gate.qubit0.accept(self)
        qubit_operand_1 = gate.qubit1.accept(self)

        if gate.name not in default_two_qubit_gate_set:
            self.output += f"{gate}\n"
        elif gate.arguments:
            arguments = ", ".join(arg.accept(self) for arg in gate.arguments)
            self.output += f"{gate.name}({arguments}) {qubit_operand_0}, {qubit_operand_1}\n"
        else:
            self.output += f"{gate.name} {qubit_operand_0}, {qubit_operand_1}\n"

    def visit_bsr_no_params(self, gate: BsrNoParams) -> str:
        return ""

    def visit_bsr_full_params(self, gate: BsrFullParams) -> str:
        nx = gate.nx.accept(self)
        ny = gate.ny.accept(self)
        nz = gate.nz.accept(self)
        theta_argument = gate.theta.accept(self)
        phi_argument = gate.phi.accept(self)
        return f"({nx}, {ny}, {nz}, {theta_argument}, {phi_argument})"

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> str:
        theta_argument = gate.theta.accept(self)
        return f"({theta_argument})"

    def visit_bsr_unitary_params(self, gate: BsrUnitaryParams) -> str:
        theta_argument = gate.theta.accept(self)
        phi_argument = gate.phi.accept(self)
        lmbda_argument = gate.lmbda.accept(self)
        return f"({theta_argument}, {phi_argument}, {lmbda_argument})"

    def visit_measure(self, measure: Measure) -> None:
        qubit_operand = measure.qubit.accept(self)
        bit_operand = measure.bit.accept(self)
        self.output += f"{bit_operand} = measure {qubit_operand}\n"

    def visit_init(self, init: Init) -> None:
        qubit_operand = init.qubit.accept(self)
        self.output += f"init {qubit_operand}\n"

    def visit_reset(self, reset: Reset) -> None:
        qubit_operand = reset.qubit.accept(self)
        self.output += f"reset {qubit_operand}\n"

    def visit_barrier(self, barrier: Barrier) -> None:
        qubit_operand = barrier.qubit.accept(self)
        self.output += f"barrier {qubit_operand}\n"

    def visit_wait(self, wait: Wait) -> None:
        time_parameter = wait.time.accept(self)
        qubit_operand = wait.qubit.accept(self)
        self.output += f"wait({time_parameter}) {qubit_operand}\n"


def circuit_to_string(circuit: Circuit) -> str:
    writer_impl = _WriterImpl(circuit.register_manager)
    circuit.ir.accept(writer_impl)

    # Remove all trailing lines and leave only one
    return writer_impl.output.rstrip() + "\n"
