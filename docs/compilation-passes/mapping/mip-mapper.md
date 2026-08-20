The MIP mapper (`MIPMapper`) pass tries to place the circuit on the quantum backend such
that qubits that need to interact end up close to each other. 
It is based on the  `place_mip` pass of
[OpenQL](https://github.com/QuTech-Delft/OpenQL/blob/develop/src/ql/pass/map/qubits/place_mip/place_mip.cc).

Unlike the [identity](identity-mapper.md), [random](random-mapper.md) and 
[hardcoded](hardcoded-mapper.md) mappers, which decide on a placement without looking at
the circuit, this pass takes the two-qubit gates into account.
It solves a _Mixed Integer Programming_ (MIP) problem to find a placement that is 
as optimal as possible for the given connectivity.

## How the mapping is computed

For every pair of virtual qubits $i$ and $j$ the pass counts how many two-qubit gates 
act on that pair, giving an interaction count $C_{ij}$.
Single-qubit gates and non-unitary instructions are ignored, as they do not constrain 
the qubit placement.
It is also computes the distance $d_{kl}$ between every pair of physical qubits $k$ and 
$l$, i.e. the length of the shortest path between them in the connectivity graph, using 
Floyd-Warshall. 
Neighbouring qubits are at distance 1.

Writing $\pi(i)$ for the physical qubit that virtual qubit $i$ is placed on, the solver 
then looks for the placement that minimizes

$$
\sum_{i,j} C_{ij} \, d_{\pi(i)\,\pi(j)},
$$

under the constraints that every virtual qubit gets exactly one physical qubit and that 
no physical qubit is used twice.

That objective is quadratic, and as such is handled by
[SciPy's `milp` solver](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.milp.html) 
in a linearized form. 
A small penalty is added for every qubit that does not stay where it was, 
which breaks ties in favour of the identity mapping.

!!! note "Mapping is not routing"

    Placing interacting qubits close together reduces the number of SWAPs a router has 
    to insert, but it does not guarantee that none are needed.
    Unless every interaction ends up between neighbouring qubits,
    a [routing pass](../routing/index.md) is still required to make the circuit 
    executable.

## Usage

The mapper needs the `connectivity` of the target backend: a dictionary mapping each
physical qubit index to the qubits it is connected to.

```python
from opensquirrel import CircuitBuilder
from opensquirrel.passes.mapper import MIPMapper

connectivity = {"0": [1], "1": [0, 2], "2": [1]}

builder = CircuitBuilder(3)
builder.H(0)
builder.CNOT(0, 1)
builder.CNOT(0, 2)
circuit = builder.to_circuit()

circuit.map(mapper=MIPMapper(connectivity=connectivity))
```

??? example "`print(circuit)`"

    ```linenums="1"
    version 3.0

    qubit[3] q

    H q[1]
    CNOT q[1], q[0]
    CNOT q[1], q[2]
    ```

The connectivity above is a line, so physical qubit `1` is the only one with two 
neighbours. 
Virtual qubit `0` is the one interacting with both others, so it is placed there, 
giving the mapping `{0: 1, 1: 0, 2: 2}` and leaving both CNOTs on neighbouring qubits.

When the circuit can already be executed on the given connectivity there is nothing to 
gain, and the tiebreaker leaves every qubit in place:

```python
builder = CircuitBuilder(3)
builder.H(0)
builder.CNOT(0, 1)
builder.CNOT(1, 2)
circuit = builder.to_circuit()

circuit.map(mapper=MIPMapper(connectivity=connectivity))
```

??? example "`print(circuit)`"

    ```linenums="1"
    version 3.0

    qubit[3] q

    H q[0]
    CNOT q[0], q[1]
    CNOT q[1], q[2]
    ```

Non-unitary instructions are remapped along with the gates. 
Each measurement follows the qubit it acts on and still writes to the same bit, 
so the meaning of the bit register is preserved:

```python
builder = CircuitBuilder(3, 3)
builder.H(0)
builder.CNOT(0, 1)
builder.CNOT(0, 2)
builder.measure(0, 0)
builder.measure(1, 1)
builder.measure(2, 2)
circuit = builder.to_circuit()

circuit.map(mapper=MIPMapper(connectivity=connectivity))
```

??? example "`print(circuit)`"

    ```linenums="1"
    version 3.0

    qubit[3] q
    bit[3] b

    H q[1]
    CNOT q[1], q[0]
    CNOT q[1], q[2]
    b[0] = measure q[1]
    b[1] = measure q[0]
    b[2] = measure q[2]
    ```

## Parameters

| Parameter      | Description                                                                  |
|----------------|------------------------------------------------------------------------------|
| `connectivity` | Connectivity of the target backend.                                          |
| `timeout`      | Maximum time, in seconds, the solver may spend. No limit by default.         |
| `epsilon`      | Penalty used to break ties towards the identity mapping. Defaults to `1e-6`. |

## When mapping fails

Finding an optimal mapping is an NP-hard problem, and the solver slows down quickly as 
the number of qubits grows. 
The `timeout` argument bounds how long it may take, but a solver that hits the limit 
raises a `RuntimeError` instead of returning a mapping:

```python
mip_mapper = MIPMapper(connectivity=connectivity, timeout=0.000001)
circuit.map(mapper=mip_mapper)
```

!!! example ""

    `RuntimeError: MIP solver failed to find a feasible mapping. Status: 1, Message: 
    Time limit reached.`

The circuit also has to fit on the backend:

!!! example ""

    `RuntimeError: Number of virtual qubits (3) exceeds number of physical qubits (2)`

Fewer virtual qubits than physical ones is fine as they are mapped onto a subset of 
them.
