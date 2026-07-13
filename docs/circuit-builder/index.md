# Circuit builder

The `CircuitBuilder` is OpenSquirrel's programmatic API for constructing a circuit. It 
offers an alternative to writing out a 
[cQASM string](../tutorial/creating-a-circuit.md#1-from-a-cqasm-string). Instead of 
describing your program as text, you assemble it instruction by instruction, directly in
Python. 

The `CircuitBuilder` may be more convenient  when the structure of your program is more 
naturally and easily expressed with code than as a static string, for instance when a 
circuit has patterns that a `for` loop captures nicely.

To get started, import the `CircuitBuilder` from `opensquirrel`:

```python
from opensquirrel import CircuitBuilder
```

## Instantiating the builder

A builder is created by declaring the sizes of its qubit and (optionally) bit registers:

```python
builder = CircuitBuilder(qubit_register_size=3, bit_register_size=2)
```

This reserves a qubit register `q` of size 3 and a bit register `b` of size 2. Qubits 
and bits are always referred to by their integer index into these registers, 
starting at `0`.

## Adding instructions

Once the builder is instantiated, instructions are added by calling the method that 
carries the name of the instruction, passing the qubit and bit indices (and any 
parameters for e.g. _parameterized gates_ ) as arguments:

```python
builder.H(0)
builder.CNOT(0, 1)
builder.Rz(2, 3.14)
```

Instruction calls can also be _chained_ together into a single expression:

```python
builder.H(0).CNOT(0, 1).CNOT(0, 2)
```

The available instructions fall into three main categories:

- [Gates](instructions/gates.md): the unitary instructions, from single-qubit gates 
such as `H`, `X` and `Rz` to two-qubit gates such as `CNOT`, abd `CZ` ,
- [Non-unitaries](instructions/non-unitaries.md): `init`, `measure` and `reset`, and
- [Control instructions](instructions/control-instructions.md): `barrier` and `wait`.

The builder checks every call as it is made. Referring to a qubit or bit that lies 
outside its register raises an `IndexError`, calling an instruction that does not exist 
raises an `AttributeError`, and passing the wrong number or type of arguments raises a 
`TypeError`.

Instructions can also be appended directly with `add_instruction`, which accepts either 
a single instruction or an iterable of them:

```python
from opensquirrel import CircuitBuilder, H, CNOT

builder = CircuitBuilder(2)
builder.add_instruction(H(0))
builder.add_instruction([H(1), CNOT(0, 1)])
circuit = builder.to_circuit()
```

## Building the circuit

Calling `to_circuit()` finalizes the construction and returns the `Circuit` object:

```python
from opensquirrel import CircuitBuilder

builder = CircuitBuilder(qubit_register_size=2)
builder.H(0)
builder.CNOT(0, 1)
circuit = builder.to_circuit()
```

??? example "`print(circuit)`"

    ```linenums="1"
    version 3.0

    qubit[2] q

    H q[0]
    CNOT q[0], q[1]
    ```

From here on, one can proceed to, for instance, 
[apply compilation passes](../tutorial/applying-compilation-passes.md) to the `circuit` 
object.

## Building circuits programmatically

Because you are building the circuit in Python, the whole language is available to 
generate the instructions. Loops, conditionals and list comprehensions make it easy to 
describe circuits whose size or structure depends on a parameter:

```python
from opensquirrel import CircuitBuilder

qubit_register_size = 10
builder = CircuitBuilder(qubit_register_size)
for qubit_index in range(0, qubit_register_size, 2):
    builder.H(qubit_index)
circuit = builder.to_circuit()
```

??? example "`print(circuit)`"

    ```linenums="1"
    version 3.0

    qubit[10] q

    H q[0]
    H q[2]
    H q[4]
    H q[6]
    H q[8]
    ```

The [tutorial](../tutorial/creating-a-circuit.md#2-by-using-the-circuit-builder) works 
through a larger example of this pattern, generating a 
[quantum Fourier transform](https://en.wikipedia.org/wiki/Quantum_Fourier_transform) of 
arbitrary size.

## Single-gate-multiple-qubit notation (SGMQ)

Instructions accept a _list_ of indices wherever they accept a single index, following 
the 
[single-gate-multiple-qubit (SGMQ) notation](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/single-gate-multiple-qubit-notation.html). 
The builder unpacks such a call into separate, consecutive instructions:

```python
builder = CircuitBuilder(3)
builder.H([0, 1, 2])
```

is equivalent to `builder.H(0).H(1).H(2)`. Any parameters are shared across the 
expansion, so `builder.Rx([0, 1, 2], math.pi / 2)` applies the same rotation to each of 
the three qubits.

For two-operand instructions, such as two-qubit gates and `measure`, both operands may 
be lists, in which case they are zipped together and must be of equal length:

```python
builder = CircuitBuilder(4)
builder.CNOT([0, 1], [2, 3])
```

adds `CNOT q[0], q[2]` followed by `CNOT q[1], q[3]`.

## Named registers

The register created by the constructor is always called `q` (and `b` for the bits). If 
you need more than one named register, for example to keep logical qubits separate from 
ancillas, start from an empty builder and add the registers yourself with `add_register`
:

```python
from opensquirrel import CircuitBuilder, QubitRegister, BitRegister

builder = CircuitBuilder()

data = QubitRegister(2, "data")
ancilla = QubitRegister(2, "ancilla")
bits = BitRegister(2, "measurement")

builder.add_register(data)
builder.add_register(ancilla)
builder.add_register(bits)

for d, a in zip(data, ancilla):
    builder.CNOT(d, a)
builder.measure(data, bits)

circuit = builder.to_circuit()
```

## Adding instructions




