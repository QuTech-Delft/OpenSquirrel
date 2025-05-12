!!! note "Coming soon"

(interim page)

# [Unitary Instructions](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/unitary_instructions.html)

| Name       | Operator       | Description                                      | Example                                                                 |
|------------|----------------|--------------------------------------------------|-------------------------------------------------------------------------|
| I          |     _I_        |               Identity gate                      | `builder.I(0)`                                                          |
| H          |     _H_        |               Hadamard gate                      | `builder.H(0)`                                                          |
| X          |     _X_        |                  Pauli-X                         | `builder.X(0)`                                                          |
| X90        | _X<sub>90</sub>_| Rotation around the x-axis of $\frac{\pi}{2}$   | `builder.X90(0)`                                                        |
| mX90       | _X<sub>-90</sub>_| Rotation around the x-axis of $\frac{-\pi}{2}$ | `builder.mX90(0)`                                                       |
| Y          |     _Y_        |                  Pauli-Y                         | `builder.Y(0)`                                                          |
| Y90        | _Y<sub>90</sub>_|  Rotation around the y-axis of $\frac{\pi}{2}$  | `builder.Y90(0)`                                                        |
| mY90       | _Y<sub>-90</sub>_| Rotation around the y-axis of $\frac{-\pi}{2}$ | `builder.mY90(0)`                                                       |
| Z          |     _Z_        |                  Pauli-Z                         | `builder.Z(0)`                                                          |
| S          |     _S_        |                 Phase gate                       | `builder.S(0)`                                                          |
| Sdag       | _S<sup>†</sup>_|                S dagger gate                     | `builder.Sdag(0)`                                                       |
| T          |     _T_        |                     T                            | `builder.T(0)`                                                          |
| Tdag       | _T<sup>†</sup>_|                T dagger gate                     | `builder.Tdag(0)`                                                       |
| Rx         | _R<sub>x</sub>($\theta$)_| Arbitrary rotation around x-axis       | `builder.Rx(0, 0.23)`                                                   |
| Ry         |  _R<sub>y</sub>($\theta$)_| Arbitrary rotation around y-axis      | `builder.Ry(0, 0.23)`                                                   |
| Rz         | _R<sub>z</sub>($\theta$)_    | 	Arbitrary rotation around z-axis | `builder.Rz(0, 2)`                                                      |
| Rn         | _R<sub>n</sub>(n<sub>x</sub>, n<sub>y</sub>, n<sub>z</sub>, $\theta$, $\phi$<sub>g</sub>)_ | Arbitrary rotation around specified axis  | `builder.Rn(0)`   |
| CZ         | _CZ_           |            Controlled-Z, Controlled-Phase        | `builder.CZ(1, 2)`                                                      |
| CR         | _CR(\theta)_   |    Controlled phase shift (arbitrary angle)      | `builder.CR(0, 1, math.pi)`                                             |
| CRk        |  _CR<sub>k</sub>(k)_   | Controlled phase shift ($\frac{\pi}{2^{k-1}}$)             | `builder.CRk(1, 0, 2)`                                |
| SWAP       |    _SWAP_      |                 SWAP gate                        | `builder.SWAP(1, 2)`                                                    |
| CNOT       |    _CNOT_      |              Controlled-NOT gate                 | `builder.CNOT(1, 2)`                                                    |
