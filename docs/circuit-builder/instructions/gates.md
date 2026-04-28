# [Unitary Instructions](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/unitary_instructions.html)

| Name  | Operator                                      | Description                                       | Example                    |
|-------|----------------                               |-------------------------------------------------- |----------------------------|
| I     | $I$                                           | Identity gate                                     | `builder.I(0)`            |
| H     | $H$                                           | Hadamard gate                                     | `builder.H(0)`            |
| X     | $X$                                           | Pauli-X                                           | `builder.X(0)`            |
| X90   | $X_{90}$                                      | Rotation around the x-axis of $\frac{\pi}{2}$     | `builder.X90(0)`          |
| mX90  | $X_{-90}$                                     | Rotation around the x-axis of $-\frac{\pi}{2}$    | `builder.mX90(0)`         |
| Y     | $Y$                                           | Pauli-Y                                           | `builder.Y(0)`            |
| Y90   | $Y_{90}$                                      | Rotation around the y-axis of $\frac{\pi}{2}$     | `builder.Y90(0)`          |
| mY90  | $Y_{-90}$                                     | Rotation around the y-axis of $-\frac{\pi}{2}$    | `builder.mY90(0)`         |
| Z     | $Z$                                           | Pauli-Z                                           | `builder.Z(0)`            |
| Z90   | $Z_{90}$                                      | Rotation around the z-axis of $\frac{\pi}{2}$     | `builder.Z90(0)`          |
| mZ90  | $Z_{-90}$                                     | Rotation around the z-axis of $-\frac{\pi}{2}$    | `builder.mZ90(0)`         |
| S     | $S$                                           | Phase gate                                        | `builder.S(0)`            |
| Sdag  | $S^\dagger$                                   | S dagger gate                                     | `builder.Sdag(0)`         |
| T     | $T$                                           | T gate                                            | `builder.T(0)`            |
| Tdag  | $T^\dagger$                                   | T dagger gate                                     | `builder.Tdag(0)`         |
| Rx    | $R_x(\theta)$                                 | Arbitrary rotation around x-axis                  | `builder.Rx(0, 0.23)`     |
| Ry    | $R_y(\theta)$                                 | Arbitrary rotation around y-axis                  | `builder.Ry(0, 0.23)`     |
| Rz    | $R_z(\theta)$                                 | Arbitrary rotation around z-axis                  | `builder.Rz(0, 2)`        |
| Rn    | $R_\textbf{n}(n_x, n_y, n_z, \theta, \phi_g)$ | Arbitrary rotation around specified axis          | `builder.Rn(0)`           |
| U     | $U(\theta, \phi,\lambda)$                     | Arbitrary unitary gate                            | `builder.U(0, 1, 2, 3)`   |
| CZ    | $CZ$                                          | Controlled-Z, Controlled-Phase                    | `builder.CZ(1, 2)`        |
| CR    | $CR(\theta)$                                  | Controlled phase shift (arbitrary angle)          | `builder.CR(0, 1, 3.1415)`|
| CRk   | $CR_k(k)$                                     | Controlled phase shift ($\frac{\pi}{2^{k-1}}$)    | `builder.CRk(1, 0, 2)`    |
| SWAP  | $SWAP$                                        | SWAP gate                                         | `builder.SWAP(1, 2)`      |
| CNOT  | $CNOT$                                        | Controlled-NOT gate                               | `builder.CNOT(1, 2)`      |
