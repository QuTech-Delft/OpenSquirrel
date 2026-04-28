# Non-Unitary Instructions

| Name       | Operator       | Description                                      | Example                                                                 |
|------------|----------------|--------------------------------------------------|-------------------------------------------------------------------------|
| [Init](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/init_instruction.html) | _init_ | Initialize the qubit in $\vert0\rangle$ | `builder.init(0)` |
| [Measure](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/measure_instruction.html) | _measure_ | Measures the qubit (by default in the Z-basis) and stores the outcome in the specified bit | `builder.measure(0, 0)` |
| [Reset](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/reset_instruction.html) | _reset_ | Resets the state of the qubit to $\vert0\rangle$ | `builder.reset(0)` |
