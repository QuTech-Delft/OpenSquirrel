# Control Instructions

| Name       | Operator       | Description                                      | Example                                                                 |
|------------|----------------|--------------------------------------------------|-------------------------------------------------------------------------|
| [Barrier](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/control_instructions/barrier_instruction.html) | _barrier_ | Places a barrier on specified qubit(s) | `builder.barrier(0)` |
| [Wait](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/control_instructions/wait_instruction.html) | _wait_ | Enforces given cycle times between consecutive instructions on specified qubit | `builder.wait(5, 0)` |
