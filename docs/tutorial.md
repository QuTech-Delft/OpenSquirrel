# Tutorial

## Installation

OpenSquirrel is available through the Python Package Index ([PyPI](<https://pypi.org/project/opensquirrel/>)). Accordingly, the installation is as easy as ABC:

```python
! pip
install
opensquirrel

import open_squirrel
```

## Creating a circuit

OpenSquirrel's entrypoint is the `Circuit`, which represents a quantum circuit. You can create a circuit in two different ways:
 1. form a string written in the cQASM 3.0 quantum programming language, or;
 2. by using OpenSquirrel's `CircuitBuilder` in Python.

### 1. From a cQASM 3.0 string

```python
from open_squirrel import Circuit

my_circuit = Circuit.from_string(
    """
    version 3.0

    qubit[2] q
    h q[0]; cnot q[0], q[1] // Create a Bell pair
    """
)
my_circuit
```

    version 3.0

    qubit[2] q

    h q[0]
    cnot q[0], q[1]

>__Note__: Currently OpenSquirrel only supports a limited version of the quantum programming language cQASM 3.0. This is due to the fact that the latter is still under development. When new features are introduced to the language, OpenSquirrel will follow in due course. For example, at the time of writing, OpenSquirrel only supports the declaration of a single qubit register per quantum program, whereas the language already allows for the declaration of multiple qubit registers within the global scope of the quantum program. Both the language and OpenSquirrel are under continuous development. Nevertheless, the language features that _are_ supported by OpenSquirrel function properly.

### 2. Using OpenSquirrel's `CircuitBuilder`

For creation of a circuit through Python, the `CircuitBuilder` can be used accordingly:

```python
from open_squirrel import CircuitBuilder
from open_squirrel.ir import Qubit, Int, Float

my_circuit_from_builder = CircuitBuilder(qubit_register_size=2).ry(Qubit(0), Float(0.23)).cnot(Qubit(0),
                                                                                               Qubit(1)).to_circuit()
my_circuit_from_builder
```

    version 3.0

    qubit[2] q

    ry q[0], 0.23
    cnot q[0], q[1]

You can naturally use the functionalities available in Python to create your circuit:

```python
builder = CircuitBuilder(qubit_register_size=10)
for i in range(0, 10, 2):
    builder.h(Qubit(i))

builder.to_circuit()
```

    version 3.0

    qubit[10] q

    h q[0]
    h q[2]
    h q[4]
    h q[6]
    h q[8]

For instance, you can generate a quantum fourier transform (QFT) circuit as follows:

```python
qubit_register_size = 5
qft = CircuitBuilder(qubit_register_size)
for i in range(qubit_register_size):
      qft.h(Qubit(i))
      for c in range(i + 1, qubit_register_size):
            qft.crk(Qubit(c), Qubit(i), Int(c-i+1))

qft.to_circuit()
```

    version 3.0

    qubit[5] q

    h q[0]
    crk q[1], q[0], 2
    crk q[2], q[0], 3
    crk q[3], q[0], 4
    crk q[4], q[0], 5
    h q[1]
    crk q[2], q[1], 2
    crk q[3], q[1], 3
    crk q[4], q[1], 4
    h q[2]
    crk q[3], q[2], 2
    crk q[4], q[2], 3
    h q[3]
    crk q[4], q[3], 2
    h q[4]

### Strong types

As you can see, gates require _strong types_. For instance, you cannot do:

```python
try:
    Circuit.from_string(
        """
        version 3.0
        qubit[2] q

        cnot q[0], 3 // The CNOT expects a qubit as second argument.
        """,
        use_libqasm=True
    )
except Exception as e:
    print(e)
```

    Parsing error: Error at <unknown>:5:9..13: failed to resolve overload for cnot with argument pack (qubit, int)

The issue is that the CNOT expects a qubit as second input argument, where an integer has been provided.

The same holds for the `CircuitBuilder`, _i.e._, it also throws an error if arguments are passed of an unexpected type:

```python
try:
    CircuitBuilder(qubit_register_size=2).cnot(Qubit(0), Int(3))
except Exception as e:
    print(e)
```

    Wrong argument type for gate `cnot`, got <class 'open_squirrel.ir.Int'> but expected <class 'open_squirrel.ir.Qubit'>

## Modifying a circuit

### Merging gates

OpenSquirrel can merge consecutive quantum gates. Currently, this is only done for single-qubit gates. The resulting gate is labeled as an "anonymous gate". Since those gates have no name, the placeholder `<anonymous-gate>` is used instead.

```python
import math

builder = CircuitBuilder(qubit_register_size=1)
for i in range(16):
  builder.rx(Qubit(0), Float(math.pi / 16))

circuit = builder.to_circuit()

# Merge single qubit gates
circuit.merge_single_qubit_gates()
circuit
```

    version 3.0

    qubit[1] q

    <anonymous-gate>

You can inspect what the gate has become in terms of the Bloch sphere rotation it represents:

```python
circuit.ir.statements[0]
```

    BlochSphereRotation(Qubit[0], axis=[1. 0. 0.], angle=3.141592653589795, phase=0.0)

In the above example, OpenSquirrel has merged all the Rx gates together. Yet, for now, OpenSquirrel does not recognize that this results in a single Rx over the cumulated angle of the individual rotations. Moreover, it does not recognize that the result corresponds to the X-gate (up to a global phase difference). At a later stage, we may want OpenSquirrel to recognize the resultant gate in the case it is part of the set of known gates.

The gate set is, however, not immutable. In the following section, we demonstrate how new gates can be defined and added to the default gate set.

### Defining your own quantum gates

OpenSquirrel accepts any new gate and requires its definition in terms of a semantic. Creating new gates is done using Python functions, decorators, and one of the following gate semantic classes: `BlochSphereRotation`, `ControlledGate`, or `MatrixGate`.

- The `BlochSphereRotation` class is used to define an arbitrary single qubit gate. It accepts a qubit, an axis, an angle, and a phase as arguments. Below is shown how the X-gate is defined in the default gate set of OpenSquirrel:

```python
@named_gate
def x(q: Qubit) -> Gate:
    return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2)
```

Notice the `@named_gate` decorator. This _tells_ OpenSquirrel that the function defines a gate and that it should, therefore, have all the nice properties OpenSquirrel expects of it. When you define a gate as such, it also creates a gate in the accompanying cQASM 3.0 parser taking the same arguments as the Python function.

- The `ControlledGate` class is used to define a multiple qubit gate that comprises a controlled operation. For instance, the CNOT gate is defined in the default gate set of OpenSquirrel as follows:

```python
@named_gate
def cnot(control: Qubit, target: Qubit) -> Gate:
    return ControlledGate(control, x(target))
```

- The `MatrixGate` class may be used to define a gate in the generic form of a matrix:

```python
@named_gate
def swap(q1: Qubit, q2: Qubit) -> Gate:
    return MatrixGate(
        np.array(
            [
                [1, 0, 0, 0],
                [0, 0, 1, 0],
                [0, 1, 0, 0],
                [0, 0, 0, 1],
            ]
        ),
        [q1, q2],
    )
```

Once you have defined your new quantum gates, you can pass them as a custom `gate_set` argument to the `Circuit` object. Here is how to add, _e.g._, the Sycamore gate (labeled as `syc`) on top of the existing default gate set of OpenSquirrel:

```python
import numpy as np
import cmath
from open_squirrel import default_gates
from open_squirrel.ir import named_gate, MatrixGate


# Definition of the Sycamore gate as a MatrixGate
@named_gate
def syc(q1: Qubit, q2: Qubit):
    return MatrixGate(
        matrix=np.array([
            [1, 0, 0, 0],
            [0, 0, -1j, 0],
            [0, -1j, 0, 0],
            [0, 0, 0, cmath.rect(1, - math.pi / 6)]
        ]),
        operands=[q1, q2]
    )


my_extended_gate_set = default_gates.default_gate_set.copy()
my_extended_gate_set.append(syc)

my_sycamore_circuit = Circuit.from_string(
    """
    version 3.0
    qubit[3] q

    h q[1]
    syc q[1], q[2]
    cnot q[0], q[1]
    """,
    gate_set=my_extended_gate_set
)
```

### Gate decomposition

OpenSquirrel can decompose the gates of a quantum circuit, given a specific decomposition. OpenSquirrel offers several, so-called, decomposers out of the box, but users can also make their own decomposer and apply them to the circuit. Decompositions can be:
   1. predefined, or;
   2. inferred from the gate semantics.

#### 1. Predefined decomposition

The first kind of decomposition is when you want to replace a particular gate in the circuit, like the CNOT gate, with a fixed list of gates. It is commonly known that CNOT can be decomposed as H-CZ-H. This decomposition is demonstrated below using a Python _lambda function_, which requires the same parameters as the gate that is decomposed:

```python
from open_squirrel.default_gates import cnot, h, cz

circuit = Circuit.from_string(
    """
    version 3.0
    qubit[3] q

    x q[0:2]  // Note that this notation is expanded in OpenSquirrel.
    cnot q[0], q[1]
    ry q[2], 6.78
    """
)

circuit.replace(cnot,
                lambda control, target:
                [
                    h(target),
                    cz(control, target),
                    h(target),
                ]
                )
circuit
```

    version 3.0

    qubit[3] q

    x q[0]
    x q[1]
    x q[2]
    h q[1]
    cz q[0], q[1]
    h q[1]
    ry q[2], 6.78

OpenSquirrel will check whether the provided decomposition is correct. For instance, an exception is thrown if we forget the final Hadamard, or H-gate, in our custom-made decomposition:

```python
circuit = Circuit.from_string(
    """
    version 3.0
    qubit[3] q

    x q[0:2]
    cnot q[0], q[1]
    ry q[2], 6.78
    """
)

try:
  circuit.replace(cnot,
                  lambda control, target:
                  [
                      h(target),
                      cz(control, target),
                  ]
)

except Exception as e:
  print(e)
```

    Replacement for gate cnot does not preserve the quantum state

#### 2. Inferred decomposition

On top of decompositions of a single gate, OpenSquirrel can decompose gates _based on their semantics_, regardless of name. To give an example, let us decompose an arbitrary single qubit gate into a product of axis rotations ZYZ; note that these are not Y- and Z-gates, but Ry and Rz rotations gates.

First, we need to figure out the mathmatics behind this decomposition. Let us use quaternions and the Python library for symbolic mathematics [SymPy](https://www.sympy.org/en/index.html) for this; it will make things a lot easier. A 3D rotation of angle $\alpha$ about the (normalized) axis $n=\left(n_x, n_y, n_z \right)$ can be represented by the quaternion $q = \cos\left(\alpha/2\right) + \sin\left(\alpha/2\right) \left( n_x i + n_y j + n_z k \right)$. Since composition of rotations is equivalent to the product of their quaternions, we have to find the angles $\theta_1$, $\theta_2$ and $\theta_3$ such that

$$\begin{align}
q =
&\left[ \cos\left(\frac{\theta_1}{2}\right) + k \sin\left(\frac{\theta_1}{2}\right) \right]\\
&\times\left[ \cos\left(\frac{\theta_2}{2}\right) + j \sin\left(\frac{\theta_2}{2}\right) \right]\\
&\times\left[ \cos\left(\frac{\theta_3}{2}\right) + k \sin\left(\frac{\theta_3}{2}\right) \right]\ .
\end{align}
$$

Let us expand this last term with SymPy:

```python
! pip install sympy
```

```python
import sympy as sp

theta1, theta2, theta3 = sp.symbols("theta_1 theta_2 theta_3")

z1 = sp.algebras.Quaternion.from_axis_angle((0, 0, 1), theta1)
y = sp.algebras.Quaternion.from_axis_angle((0, 1, 0), theta2)
z2 = sp.algebras.Quaternion.from_axis_angle((0, 0, 1), theta3)

rhs = sp.trigsimp(sp.expand(z1 * y * z2))
rhs
```

$$ \cos{\left(\frac{\theta_{2}}{2} \right)} \cos{\left(\frac{\theta_{1} + \theta_{3}}{2} \right)} + - \sin{\left(\frac{\theta_{2}}{2} \right)} \sin{\left(\frac{\theta_{1} - \theta_{3}}{2} \right)} i + \sin{\left(\frac{\theta_{2}}{2} \right)} \cos{\left(\frac{\theta_{1} - \theta_{3}}{2} \right)} j + \sin{\left(\frac{\theta_{1} + \theta_{3}}{2} \right)} \cos{\left(\frac{\theta_{2}}{2} \right)} k$$

Let us change variables and define $p\equiv\theta_1 + \theta_3$ and $m\equiv\theta_1 - \theta_3$.

```python
p, m = sp.symbols("p m")

rhs_simplified = rhs.subs({
    theta1 + theta3: p,
    theta1 - theta3: m
})

rhs_simplified
```

$$ \cos{\left(\frac{p}{2} \right)} \cos{\left(\frac{\theta_{2}}{2} \right)} + - \sin{\left(\frac{m}{2} \right)} \sin{\left(\frac{\theta_{2}}{2} \right)} i + \sin{\left(\frac{\theta_{2}}{2} \right)} \cos{\left(\frac{m}{2} \right)} j + \sin{\left(\frac{p}{2} \right)} \cos{\left(\frac{\theta_{2}}{2} \right)} k$$

The original quaternion $q$ can be defined in Sympy accordingly:

```python
alpha, nx, ny, nz = sp.symbols("alpha n_x n_y n_z")

q = sp.algebras.Quaternion.from_axis_angle((nx, ny, nz), alpha).subs({
    nx**2 + ny**2 + nz**2: 1  # We assume the axis is normalized.
})
q
```

$$ \cos{\left(\frac{\alpha}{2} \right)} + n_{x} \sin{\left(\frac{\alpha}{2} \right)} i + n_{y} \sin{\left(\frac{\alpha}{2} \right)} j + n_{z} \sin{\left(\frac{\alpha}{2} \right)} k$$

We get the following system of equations, where the unknowns are $p$, $m$, and $\theta_2$:

```python
from IPython.display import display, Math

display(
    sp.Eq(rhs_simplified.a, q.a),
    sp.Eq(rhs_simplified.b, q.b),
    sp.Eq(rhs_simplified.c, q.c),
    sp.Eq(rhs_simplified.d, q.d)
    )

```

$$ \cos{\left(\frac{p}{2} \right)} \cos{\left(\frac{\theta_{2}}{2} \right)} = \cos{\left(\frac{\alpha}{2} \right)}$$

$$ - \sin{\left(\frac{m}{2} \right)} \sin{\left(\frac{\theta_{2}}{2} \right)} = n_{x} \sin{\left(\frac{\alpha}{2} \right)}$$

$$ \sin{\left(\frac{\theta_{2}}{2} \right)} \cos{\left(\frac{m}{2} \right)} = n_{y} \sin{\left(\frac{\alpha}{2} \right)}$$

$$ \sin{\left(\frac{p}{2} \right)} \cos{\left(\frac{\theta_{2}}{2} \right)} = n_{z} \sin{\left(\frac{\alpha}{2} \right)}$$

This system can be solved using Sympy, but we obtain a rather ugly solution after some computation time:

```python
# sp.solve([q.a - rhs.a, q.b - rhs.b, q.c - rhs.c, q.d - rhs.d], theta1, theta2, theta3) # Using this we obtain a rather ugly solution after some computation time ...
```
Instead, we assume $\sin(p/2) \neq 0$, such that we can substitute in the first equation $\cos\left(\theta_2/2\right)$ with its value computed from the last equation. We find:

```python
sp.trigsimp(sp.Eq(rhs_simplified.a, q.a).subs(sp.cos(theta2 / 2), nz * sp.sin(alpha / 2) / sp.sin(p / 2)))
```

$$ \frac{n_{z} \sin{\left(\frac{\alpha}{2} \right)}}{\tan{\left(\frac{p}{2} \right)}} = \cos{\left(\frac{\alpha}{2} \right)}$$

Therefore,


$$p=\theta_1+\theta_3=2\arctan\left[n_z\tan\left(\frac{\alpha}{2}\right)\right]$$


We can then deduce


$$\begin{array}{rl}\theta_2 &=2\arccos\left[\cos\left(\frac{\alpha}{2}\right)\cos^{-1}\left(\frac{p}{2}\right)\right] \\ &=2\arccos\left[ \cos\left(\frac{\alpha}{2}\right)\sqrt{1+n_z^2\tan^2\left(\frac{\alpha}{2}\right)}\right] \\ \end{array}$$


Using the third equation, we can finally infer the value of $m$:


$$m=\theta_1-\theta_3=2\arccos\left[\frac{n_y\sin\left(\frac{\alpha}{2}\right)}{\sin\left(\frac{\theta_2}{2}\right)}\right]$$


Let us put this into code...

```python
from typing import Tuple

ATOL = 0.0001

def theta123(alpha: float, axis: Tuple[float, float, float]):
    """
    Gives the angles used in the Z-Y-Z decomposition of the Bloch sphere rotation
    characterized by a rotation around `axis` of angle `alpha`.

    Parameters:
      alpha: angle of the Bloch sphere rotation
      axis: _normalized_ axis of the Bloch sphere rotation

    Returns:
      a triple (theta1, theta2, theta3) corresponding to the decomposition of the
      arbitrary Bloch sphere rotation into U = rz(theta1) ry(theta2) rz(theta3)

    """

    # CAUTION: there might be edge cases where this crashes.

    nx, ny, nz = axis
    assert abs(nx**2 + ny**2 + nz**2 - 1) < ATOL, "Axis needs to be normalized"

    ta2 = math.tan(alpha / 2)
    theta2 = 2 * math.acos(math.cos(alpha / 2) * math.sqrt(1 + (nz * ta2) ** 2))

    p = 2 * math.atan(nz * ta2)
    m = 2 * math.acos(ny * math.sin(alpha / 2) / math.sin(theta2 / 2))

    theta1 = (p + m) / 2
    theta3 = p - theta1

    return (theta1, theta2, theta3)
```

Once we have our angles, we can implement the OpenSquirrel decomposition; we will name it the `ZYZDecomposer`. Implementation is done by inheriting from the `Decomposer` base class and defining the `decompose` method, which in turn expects a gate and returns a list of gates. This method is applied internally to all gates of the circuit. Since 2-qubit gates should be left as-is, there is an `isinstance` check, to skip those. Also note that the axis of a `BlochSphereRotation` in OpenSquirrel is always normalized internally, and the _angle_ should always be in the range $[-\pi, \pi]$.

Here is what our final ZYZ decomposition looks like:

```python
from open_squirrel.ir import Gate, BlochSphereRotation
from open_squirrel.decomposer.general_decomposer import Decomposer
from open_squirrel.default_gates import rz, ry


class ZYZDecomposer(Decomposer):

    def decompose(g: Gate) -> [Gate]:
        if not isinstance(g, BlochSphereRotation):
            return [g]  # Do nothing.

        theta1, theta2, theta3 = theta123(g.angle, g.axis)

        z1 = rz(g.qubit, Float(theta1))
        y = ry(g.qubit, Float(theta2))
        z2 = rz(g.qubit, Float(theta3))

        # Note: written like this, the decomposition doesn't preserve the global phase, which is fine
        # since the global phase is a physically irrelevant artifact of the mathematical
        # model we use to describe the quantum system.

        # Should we want to preserve it, we would need to use a raw BlochSphereRotation, which would then
        # be an anonymous gate in the resulting decomposed circuit:
        # z2 = BlochSphereRotation(qubit=g.qubit, angle=theta3, axis=(0, 0, 1), phase = g.phase)

        return [z1, y, z2]
```

Once we defined the decomposition function, we can apply it by passing our decomposer to the `decompose()` method of the circuit. The decomposition of every gate is checked, to see if it preserves the circuit semantics (_i.e._, the unitary matrix), so we can sleep on both ears knowing that our circuit/quantum state remains the same.


```python
circuit_to_decompose = Circuit.from_string(
    """
    version 3.0

    qubit[3] q

    h q[0]
    """
)

circuit_to_decompose.merge_single_qubit_gates()
circuit_to_decompose.decompose(decomposer=ZYZDecomposer)
circuit_to_decompose
```

    version 3.0

    qubit[3] q

    rz q[0], 3.1415927
    ry q[0], 1.5707963
    rz q[0], 0.0

We get the expected result for the Hadamard gate: H = Y$^{1/2}$Z, one of the canonical decompositions of the Hadamard gate as described in the [Quantum Inspire knowledge base](https://www.quantum-inspire.com/kbase/hadamard/).

## Exporting a circuit

As you have seen in the examples above, you can turn a circuit into a cQASM 3.0 string by simply using the `str` or `__repr__` methods. We are aiming to support the possibility to export to other languages as well, _e.g._, a OpenQASM 3.0 string, and frameworks, _e.g._, a Qiskit quantum circuit.
