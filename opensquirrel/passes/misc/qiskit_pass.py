# %%
from typing import Any
import copy
from abc import abstractmethod
import qiskit

from opensquirrel import CNOT, Circuit
from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager

from opensquirrel.ir import Gate, IR
from opensquirrel.passes.decomposer.general_decomposer import Decomposer
from qiskit import transpile, QuantumCircuit
from opensquirrel.passes.router.general_router import Router, Connectivity
from opensquirrel.passes.exporter import qiskit_circuit_exporter
from opensquirrel.utils import qiskit_importer


class QiskitPass(Router):  # Noto: Decomposer is not entirely the right base class
    def __init__(self, *args, connectivity: Connectivity | None = None, **kwargs: Any) -> None:
        """General pass via a Qiskit pass"""
        connectivity = connectivity or {}

        super().__init__(*args, connectivity=connectivity, **kwargs)

    @abstractmethod
    def qiskit_pass(self, circuit: QuantumCircuit) -> QuantumCircuit: ...

    def route(self, ir: IR, qubit_register_size: int) -> IR:
        bit_register_size = qubit_register_size  # hmmm
        register_manager = RegisterManager(QubitRegister(qubit_register_size), BitRegister(bit_register_size))
        circuit = Circuit(copy.deepcopy(register_manager), copy.deepcopy(ir))
        qiskit_circuit, _ = qiskit_circuit_exporter.export(circuit)

        # print(qiskit_circuit.draw())
        updated_qiskit_circuit = self.qiskit_pass(qiskit_circuit)
        self.latest_updated_qiskit_circuit = updated_qiskit_circuit
        # print(updated_qiskit_circuit.draw())

        os_circuit = updated_qiskit_circuit
        os_circuit = qiskit_importer.circuit_to_opensquirrel(updated_qiskit_circuit)

        return os_circuit


class QiskitBasisTranslator(QiskitPass):  # Noto: Decomposer is not entirely the right base class
    def __init__(self, *args, basis_gates: tuple[str], **kwargs: Any) -> None:
        self.basis_gates = basis_gates
        super().__init__(*args, **kwargs)

    def qiskit_pass(self, circuit: QuantumCircuit) -> QuantumCircuit:
        print(f"QiskitBasisTranslator: {self.basis_gates}")
        return transpile(circuit, basis_gates=self.basis_gates)


class QiskitOptimize1qGates(QiskitPass):  # Noto: Decomposer is not entirely the right base class
    def __init__(self, *args, **kwargs: Any) -> None:
        self.qpass = qiskit.transpiler.passes.Optimize1qGates(*args, **kwargs)

        super().__init__()

    def qiskit_pass(self, circuit: QuantumCircuit) -> QuantumCircuit:
        return self.qpass(circuit.decompose())


if __name__ == "__main__":
    from numpy.random import default_rng
    from ptetools.tools import cprint
    from rich import print as rprint

    from opensquirrel import CNOT, SWAP
    from opensquirrel import CircuitBuilder

    builder = CircuitBuilder(qubit_register_size=3, bit_register_size=3)
    builder.H(0)
    builder.CNOT(0, 1)
    builder.measure(0, 0)
    builder.measure(1, 1)

    circuit = builder.to_circuit()
    print(f"Input circuit:")
    cprint(f"{circuit}")

    qiskit_circuit, _ = qiskit_circuit_exporter.export(circuit)
    # qiskit_importer.circuit_to_opensquirrel(qiskit_circuit)

    qpass = QiskitBasisTranslator(basis_gates=("cz", "sx", "rz"))
    new_ir = qpass.route(circuit.ir, circuit.qubit_register_size)
    print(f"Output {qpass.basis_gates}")
    cprint(new_ir)

    qpass = QiskitBasisTranslator(basis_gates=("cx", "ry", "rx"))
    new_ir = qpass.route(circuit.ir, circuit.qubit_register_size)
    print(f"Output {qpass.basis_gates}")
    cprint(new_ir)

    qpass = QiskitBasisTranslator(basis_gates=("cz", "h"))
    new_ir = qpass.route(circuit.ir, circuit.qubit_register_size)
    print(f"Output {qpass.basis_gates}")
    cprint(new_ir)

    builder = CircuitBuilder(qubit_register_size=3, bit_register_size=3)
    builder.H(0)
    builder.H(1)
    builder.Rx(0, 0.1)

    circuit = builder.to_circuit()
    print(f"Input circuit:")
    cprint(f"{circuit}")

    qpass = QiskitOptimize1qGates()
    new_ir = qpass.route(circuit.ir, circuit.qubit_register_size)
    print(f"Output {qpass}")
    cprint(new_ir)

    # decomposer = SWAP2CNOTDecomposer(system_calibration=system_calibration)
    # r = decomposer.decompose(gate)
    # cprint("With configuration")
    # rprint(r)
