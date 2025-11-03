"""
Apache License 2.0: vendored from quantuminspire-qiskit

"""

from typing import Any
from typing import SupportsFloat
import math
from qiskit import QuantumCircuit
from qiskit.circuit import CircuitInstruction

from opensquirrel import CircuitBuilder
from opensquirrel.ir import Bit, Qubit
from opensquirrel.writer import writer

from opensquirrel.ir import Axis, AxisLike, QubitLike
from opensquirrel.ir.semantics import BsrAngleParam, BsrFullParams, BsrNoParams
from opensquirrel.ir.default_gates import Rn


class U(BsrFullParams):
    def __init__(
        self,
        qubit: QubitLike,
        theta: SupportsFloat,
        phi: SupportsFloat,
        lmbda: SupportsFloat,
    ) -> None:
        from opensquirrel.passes.merger.general_merger import compose_bloch_sphere_rotations  # lazy import

        a = Rn(qubit, 0, 0, 1, lmbda, phi=0)
        b = Rn(qubit, 0, 1, 0, theta, phi=0)
        c = Rn(qubit, 0, 0, 1, phi, phi=(float(phi) + float(lmbda)) / 2)
        bsr = compose_bloch_sphere_rotations(compose_bloch_sphere_rotations(a, b), c)
        BsrFullParams.__init__(self, qubit=qubit, axis=bsr.axis, angle=bsr.angle, phase=bsr.phase, name="U")


class U2(BsrFullParams):
    def __init__(
        self,
        qubit: QubitLike,
        # theta: SupportsFloat,
        phi: SupportsFloat,
        lmbda: SupportsFloat,
    ) -> None:
        from opensquirrel.passes.merger.general_merger import compose_bloch_sphere_rotations  # lazy import

        theta = math.pi / 2
        a = Rn(qubit, 0, 0, 1, lmbda, phi=0)
        b = Rn(qubit, 0, 1, 0, theta, phi=0)
        c = Rn(qubit, 0, 0, 1, phi, phi=(float(phi) + float(lmbda)) / 2)
        bsr = compose_bloch_sphere_rotations(compose_bloch_sphere_rotations(a, b), c)
        BsrFullParams.__init__(self, qubit=qubit, axis=bsr.axis, angle=bsr.angle, phase=bsr.phase, name="U2")


_DEFAULT_QISKIT_TO_OPENSQUIRREL_MAPPING: dict[str, str] = {
    "id": "I",
    "h": "H",
    "x": "X",
    "y": "Y",
    "z": "Z",
    "s": "S",
    "sx": "X90",  # close, but phase is different
    "sdg": "Sdag",
    "t": "T",
    "tdg": "Tdag",
    "rx": "Rx",
    "ry": "Ry",
    "rz": "Rz",
    "cx": "CNOT",
    "cz": "CZ",
    "u": U,
    "u2": U2,
    "cp": "CR",
    "swap": "SWAP",
    "measure": "measure",
    "reset": "reset",
    "barrier": "barrier",
    "delay": "wait",
    "ccx": "toffoli",
}


class InstructionMapping:
    def __init__(self, qiskit_to_os: dict[str, str] = _DEFAULT_QISKIT_TO_OPENSQUIRREL_MAPPING):
        self._QISKIT_TO_OPENSQUIRREL_MAPPING: dict[str, str] = qiskit_to_os
        # Uses lower case for keys to normalize inconsistent capitalization of backends
        self._OPENSQUIRREL_TO_QISKIT_MAPPING: dict[str, str] = {
            v.lower() if isinstance(v, str) else v: k for k, v in self._QISKIT_TO_OPENSQUIRREL_MAPPING.items()
        }

    def qiskit_to_opensquirrel(self, instruction: str) -> str:
        """Translate a Qiskit gate name to the equivalent opensquirrel gate name."""
        return self._QISKIT_TO_OPENSQUIRREL_MAPPING[instruction.lower()]

    def opensquirrel_to_qiskit(self, instruction: str) -> str:
        """Translate an opensquirrel gate name to the equivalent Qiskit gate name."""
        return self._OPENSQUIRREL_TO_QISKIT_MAPPING[instruction.lower()]

    def supported_opensquirrel_instructions(self) -> list[str]:
        """Return a list of all supported opensquirrel instructions."""
        return list(self._QISKIT_TO_OPENSQUIRREL_MAPPING.values())

    def supported_qiskit_instructions(self) -> list[str]:
        """Return a list of all supported Qiskit instructions."""
        return list(self._QISKIT_TO_OPENSQUIRREL_MAPPING.keys())


_INSTRUCTION_MAPPING = InstructionMapping()


def _add_instruction(builder: CircuitBuilder, circuit_instruction: Any) -> None:
    operation = circuit_instruction.operation
    name = operation.name
    params = [param for param in operation.params]
    qubit_operands = [Qubit(qubit._index) for qubit in circuit_instruction.qubits]
    clbit_operands = [Bit(clbit._index) for clbit in circuit_instruction.clbits]

    try:
        # Get the gate's method in the CircuitBuilder class, call with operands
        # All of the builder's methods follow the same pattern, first the qubit operands, then parameters
        # Only method with classical bit operands is measure, which does not have parameters
        qname = _INSTRUCTION_MAPPING.qiskit_to_opensquirrel(name)
        if isinstance(qname, str):
            getattr(builder, qname)(*qubit_operands, *clbit_operands, *params)
        else:
            # temporary
            instr = qname(*qubit_operands, *clbit_operands, *params)
            builder.ir.add_statement(instr)

    except KeyError:
        raise NotImplementedError(
            f"Unsupported instruction: {name}. Please edit your circuit or use Qiskit transpilation to support "
            "your selected backend."
        )


def circuit_to_opensquirrel(circuit: QuantumCircuit) -> Any:
    """Return the cQASM representation of the circuit."""
    builder = CircuitBuilder(circuit.num_qubits, circuit.num_clbits)
    for circuit_instruction in circuit.data:
        operation = circuit_instruction.operation
        name = operation.name

        if name == "delay":
            if circuit_instruction.operation.unit != "dt":
                raise NotImplementedError(
                    f"Unsupported delay unit {circuit_instruction.operation.unit} in: {circuit_instruction}. Only 'dt'"
                    " is supported."
                )

        if name == "barrier":
            # Opensquirrel does not support multi-qubit barriers.
            for qubit in circuit_instruction.qubits:
                _add_instruction(builder, CircuitInstruction(operation=operation, qubits=[qubit]))
        elif name == "asm":
            getattr(builder, name)(*operation.params)
        else:
            _add_instruction(builder, circuit_instruction)

    return builder.to_circuit()


def dumps(circuit: QuantumCircuit) -> str:
    """Return the cQASM representation of the circuit."""
    os_circuit = circuit_to_opensquirrel(circuit)

    cqasm: str = writer.circuit_to_string(os_circuit)

    return cqasm


if __name__ == "__main__":
    import opensquirrel
    from qiskit import QuantumCircuit

    builder = CircuitBuilder(2, 2)

    qc = QuantumCircuit(2, 1)
    qc.rx(0.1, 0)
    qc.barrier()
    # parity measurement
    qc.cx(0, 1)
    qc.barrier()
    qc.sx(0)
    qc.u(0.1, 0.2, 0.3, 0)
    qc.measure(1, 0)
    qc.cx(0, 1)

    c = circuit_to_opensquirrel(qc)

    dumps(qc)

    print(c)
