from circuit import Circuit
from passes.decomposer import DecomposerInferred, DecomposerPredefined
from passes.writer import WriterX

if __name__ == '__main__':

    target_info = {
        "native_gate_set": {"Rx", "CZ"}
    }

    circuit_string = "circuit"
    qc = Circuit(circuit_string)

    qc.decompose(decomposer=DecomposerInferred)
    qc.decompose(decomposer=DecomposerPredefined, target_info=target_info)

    compiled_circuit = qc.write(writer=WriterX)
    print(compiled_circuit)
