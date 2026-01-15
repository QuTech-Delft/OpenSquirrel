from opensquirrel.passes.mapper import MIPMapper
from opensquirrel import Circuit, CircuitBuilder

# connectivity = {"0": [1], "1": [0, 2], "2": [1, 3], "3": [2, 4], "4": [3]}

# circuit = Circuit.from_string(
# """version 3.0; qubit[5] q; bit[2] b; H q[0]; CNOT q[0], q[1]; b = measure q[0, 1]""")

# circuit.map(mapper=MIPMapper(connectivity=connectivity))

# print(circuit)

# connectivity = {"0": [1], "1": [2, 0], "2": [1]}

# builder = CircuitBuilder(3)
# builder.CNOT(0, 1)
# builder.CNOT(0, 2)
# circuit = builder.to_circuit()

# circuit.map(mapper=MIPMapper(connectivity=connectivity))

# print(circuit)

connectivity1 = {"0": [1, 2], "1": [0, 2, 3], "2": [0, 1, 4], "3": [1, 4], "4": [2, 3]}

builder = CircuitBuilder(5)
builder.H(0)
builder.CNOT(0, 1)
builder.H(2)
builder.CNOT(1, 2)
builder.CNOT(2, 4)
builder.CNOT(3, 4)
circuit1 = builder.to_circuit()

circuit1.map(mapper=MIPMapper(connectivity=connectivity1))

print(circuit1)

connectivity2 = {"0": [1, 2], "1": [0, 3], "2": [0, 4], "3": [1, 5], "4": [2, 5], "5": [3, 4, 6], "6": [5]}

builder = CircuitBuilder(7)
builder.H(0)
builder.CNOT(0, 1)
builder.CNOT(0, 3)
builder.H(2)
builder.CNOT(1, 2)
builder.CNOT(1, 3)
builder.CNOT(2, 3)
builder.CNOT(3, 4)
builder.CNOT(0, 4)
circuit2 = builder.to_circuit()

mapper = MIPMapper(connectivity=connectivity2)

mapping = mapper.map(circuit2.ir, circuit2.qubit_register_size)

print(mapping.items())

circuit2.map(mapper=MIPMapper(connectivity=connectivity2))

print(circuit2)

builder = CircuitBuilder(7)
builder.H(0)
builder.CNOT(0, 1)
builder.CNOT(0, 2)
builder.CNOT(1, 3)
builder.CNOT(2, 4)
builder.CNOT(3, 5)
builder.CNOT(4, 6)
circuit3 = builder.to_circuit()

builder = CircuitBuilder(4)
builder.H(0)
builder.CNOT(0, 1)
builder.CNOT(1, 2)
builder.CNOT(1, 2)
builder.CNOT(2, 3)
circuit4 = builder.to_circuit()

mapper = MIPMapper(connectivity=connectivity1)

mapping = mapper.map(circuit4.ir, circuit4.qubit_register_size)

print(mapping.items())




