The cQASM v1 exporter (`CQasmV1Exporter`) exports the circuit to a string that adheres to the
[cQASM version 1.0 language specification](https://libqasm.readthedocs.io/).

Here are some important differences to take note of:

1. The [version statement](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/version_statement.html)
changes from `version 3.<m>` (where `<m>` refers to the _minor_ version number) to `version 1.0`.
2. All [qubit register declarations](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/variable_declarations/qubit_register_declaration.html)
are combined into a single (virtual) qubit register (`q`) statement.
3. [Bit registers declarations](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/variable_declarations/bit_register_declaration.html)
and [assignments of measurement outcomes to bit register variables](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/measure_instruction.html)
are discarded; cQASM version 1.0 does not support bit registers or variables.
Note that the measurement statement is not discarded; the `measure` instruction is translated to
[`measure_z`](https://libqasm.readthedocs.io/en/latest/cq1-instructions.html#measure-z-qubit).
The outcome of a measurement on qubit at (virtual) index _i_ will be stored at index _i_ in the measurement register.
4. The non-unitary [`init`](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/init_instruction.html)
and [`reset`](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/reset_instruction.html)
instructions are both translated to [`prep_z`](https://libqasm.readthedocs.io/en/latest/cq1-instructions.html#prep-z-qubit).
5. [Instructions are translated to lowercase](https://libqasm.readthedocs.io/en/latest/cq1-instructions.html#prep-z-qubit);
even though, cQASM version 1.0 is not case-sensitive.
6. [Single gate multi qubit (SGMQ)](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/single-gate-multiple-qubit-notation.html)
notation is unpacked; the gate is applied to each qubit on a separate line.
7. Consecutive [`barrier`](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/control_instructions/barrier_instruction.html)
instructions are grouped in SGMQ notation to form a _uniform_ barrier, across which no instructions on the specified
qubits can be scheduled.

!!! warning "Unsupported gates"

    cQASM version 1.0 does not support the [Rn gate](https://qutech-delft.github.io/cQASM-spec/latest/standard_gate_set/single_qubit/sq_Rn.html)
    and will raise an error (`UnSupportedGateError`) if this gate is part of the circuit that is to be exported.
    A single-qubit [decomposition pass](../decomposition/index.md) can be used to decompose the circuit to gates that
    the cQASM v1 exporter supports.

The four examples below show how circuits written in [cQASM](https://qutech-delft.github.io/cQASM-spec/) are exported to
cQASM v1.

!!! example ""

    === "Simple circuit"

        ```python
        from opensquirrel import Circuit
        from opensquirrel.passes.exporter import CQasmV1Exporter
        ```

        ```python
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[2] q
            bit[2] b

            H q[0]
            CNOT q[0], q[1]
            b = measure q
            """
        )

        exported_circuit = circuit.export(exporter=CQasmV1Exporter)
        print(exported_circuit)
        ```

        ```
        version 1.0

        qubits 2

        h q[0]
        cnot q[0], q[1]
        measure_z q[0]
        measure_z q[1]
        ```

        Note that the version statement is changed (1.), the qubit register declaration is made into a statement (2.),
        the bit register declaration and assignment to bit variables have been discarded (3.),
        the instructions are in lowercase (5.), and the SGMQ notation has been unpacked (6.).
        _The numbers refer to the differences listed above._

    === "Registers"

        ```python
        from opensquirrel import Circuit
        from opensquirrel.passes.exporter import CQasmv1Exporter
        ```

        ```python
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[2] qA
            bit[3] bA

            H qA[0]
            CNOT qA[0], qA[1]

            bA[1,2] = measure qA

            qubit[3] qB
            bit[2] bB

            H qB[1]
            CNOT qB[1], qA[1]

            bB[0] = measure qB[1]
            bB[1] = measure qA[1]
            """
        )

        exported_circuit = circuit.export(exporter=CQasmv1Exporter)
        print(exported_circuit)
        ```

        ```
        version 1.0

        qubits 5

        h q[0]
        cnot q[0], q[1]
        measure_z q[0]
        measure_z q[1]
        h q[3]
        cnot q[3], q[1]
        measure_z q[3]
        measure_z q[1]
        ```

        Note that the version statement is changed (1.), the qubit register declaration is made into a statement (2.),
        the bit register declaration and assignment to bit variables have been discarded (3.),
        the instructions are in lowercase (5.), and the SGMQ notation has been unpacked (6.).
        _The numbers refer to the differences listed above._

        In particular, this example illustrates that all qubit registers have been combined into a single (virtual)
        qubit register `q`, _i.e._, the registers `qA` and `qB` have been concatenated into `q`,
        such that `qA[0], qA[1] = q[0], q[1]` and `qB[0], qB[1], qB[2] = q[2], q[3], q[4]`.
        The qubit registers are concatenated in the order they are declared.

        Moreover, the bit registers have been discarded and the measurement instructions `measure_z` _implicitly_ assign
        the measurement outcomes to the bit/measurement register index corresponding to the index of the (virtual) qubit
        that is measured. For instance, `bB[0] = measure qB[1]` is translated to `measure_z q[3]`,
        and the outcome will bestored at index 3 in the bit/measurement register.
        This also implies that different measurements on the same qubit, at (virtual) index _i_ will always be stored in
        the same place, _i.e._ at index _i_, on the bit/measurement register.
        Which further implies that outcomes of subsequent measurements on the same qubit always overwrite the outcome of
        the previous measurement.

    === "`init` and `reset`"

        ```python
        from opensquirrel import Circuit
        from opensquirrel.passes.exporter import CQasmV1Exporter
        ```

        ```python
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[2] q
            bit[2] b

            init q

            H q[0]
            CNOT q[0], q[1]
            b = measure q

            reset q

            H q[0]
            Z q[0]
            CNOT q[0], q[1]
            b = measure q
            """
        )

        exported_circuit = circuit.export(exporter=CQasmV1Exporter)
        print(exported_circuit)
        ```

        ```
        version 1.0

        qubits 2

        prep_z q[0]
        prep_z q[1]
        h q[0]
        cnot q[0], q[1]
        measure_z q[0]
        measure_z q[1]
        prep_z q[0]
        prep_z q[1]
        h q[0]
        z q[0]
        cnot q[0], q[1]
        measure_z q[0]
        measure_z q[1]
        ```

        Note that the version statement is changed (1.), the qubit register declaration is made into a statement (2.),
        the bit register declaration and assignment to bit variables have been discarded (3.),
        the `init` and `reset` instructions are both translated to `prep_z` (4.),
        the instructions are in lowercase (5.), and the SGMQ notation has been unpacked (6.).
        _The numbers refer to the differences listed above._

        In cQASM version 1.0, one cannot distinguish between an `init` and a `reset` instruction.
        The definition of the `prep_z` instruction is close to that of the `reset` instruction, _i.e._,
        the state of the qubit is set to $|0\rangle$ by first measuring it and then,
        conditioned on the outcome being 1, applying a Pauli-X gate.

    === "SGMQ notation and _uniform_ barriers"

        ```python
        from opensquirrel import Circuit
        from opensquirrel.passes.exporter import CQasmV1Exporter
        ```

        ```python
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[4] q
            bit[4] b

            init q[0,1]

            barrier q[0]

            H q[0]
            CNOT q[0], q[1]

            init q[2]

            barrier q[0]
            barrier q[1]
            barrier q[2]

            H q[2]
            b[0,1] = measure q[0,1]

            init q[3]

            barrier q[2, 3]
            Z q[2]
            CNOT q[2], q[3]

            b[2,3] = measure q[2,3]
            """
        )

        exported_circuit = circuit.export(exporter=CQasmV1Exporter)
        print(exported_circuit)
        ```

        ```
        version 1.0

        qubits 4

        prep_z q[0]
        prep_z q[1]
        barrier q[0]
        h q[0]
        cnot q[0], q[1]
        prep_z q[2]
        barrier q[0, 1, 2]
        h q[2]
        measure_z q[0]
        measure_z q[1]
        prep_z q[3]
        barrier q[2, 3]
        z q[2]
        cnot q[2], q[3]
        measure_z q[2]
        measure_z q[3]
        ```

        Note that the version statement is changed (1.), the qubit register declaration is made into a statement (2.),
        the bit register declaration and assignment to bit variables have been discarded (3.),
        the `init` instruction is translated to `prep_z` (4.),
        the instructions are in lowercase (5.), the SGMQ notation has been unpacked (6.) and consecutive `barrier`
        have been grouped in SGMQ notation to form a _uniform_ barrier (7.).
        _The numbers refer to the differences listed above._

        The three consecutive barrier instructions, following the `init q[2]` statement, have been grouped using SGMQ
        notation.
        They form a uniform barrier across all the specified qubits, instead of a single barrier on each of the
        respective qubits.
        Also, in contrast to other instructions where the SGMQ notation has been unpacked, the SGMQ notation for the
        statement `barrier q[2, 3]` has been preserved.
