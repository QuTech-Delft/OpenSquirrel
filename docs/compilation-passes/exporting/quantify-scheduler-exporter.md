The [quantify-scheduler](https://quantify-os.org/docs/quantify-scheduler/) exporter (`ExportFormat.QUANTIFY_SCHEDULER`)
exports the circuit to [`Schedule`](https://quantify-os.org/docs/quantify-scheduler/v0.25.0/autoapi/quantify_scheduler/index.html#quantify_scheduler.Schedule)
object and a _bitstring mapping_.

The latter can be used to relate the measurement outcomes to the (virtual) bit variables they have
been assigned to in the cQASM circuit: this connection is lost in the `Schedule`.

!!! warning "Under active development"

    The bitstring mapping, currently, consists of a list of ordered pairs; the first element denotes the acquisition
    index $i$ and the second element denotes the qubit index $j$.
    The acquisition index represents the $i$-th measurement on qubit at index $j$.
    The index $k$ of the ordered pair in the bitstring mapping corresponds to the index of the (virtual) bit register,
    referring to the (virtual) bit variable the outcome of measurement $(i,j)$ has been assigned to in the
    cQASM circuit.

    ```python
    [
        (<acquisition-index-i: int>, <qubit-index-j: int>),
        (<acquisition-index-i: int>, <qubit-index-j: int>),
        ...
        <(i,j)-at-index-k: tuple[int, int]>,
        ...
    ]
    ```

    _A redesign of the bitstring mapping is under active development._

Here are some important differences to take note of:

1. All [qubit register declarations](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/variable_declarations/qubit_register_declaration.html)
are combined into a single (virtual) qubit register (`q`) statement.
2. [Bit registers declarations](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/variable_declarations/bit_register_declaration.html)
and [assignments of measurement outcomes to bit register variables](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/measure_instruction.html)
are discarded; quantify-scheduler does not support bit registers or variables.
Note that the measurement statement is not discarded; the `measure` instruction is translated to
[`Measure`](https://quantify-os.org/docs/quantify-scheduler/v0.25.0/autoapi/quantify_scheduler/operations/gate_library/index.html#quantify_scheduler.operations.gate_library.Measure).
Furthermore, measurement outcomes are related to the (virtual) bit registers they were assigned to in the cQASM circuit
through the _bitstring mapping_, as described above.
3. The non-unitary [`init`](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/init_instruction.html)
instruction is ignored and [`reset`](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/non_unitary_instructions/reset_instruction.html)
instruction is translated to [`Reset`](https://quantify-os.org/docs/quantify-scheduler/v0.25.0/autoapi/quantify_scheduler/operations/gate_library/index.html#quantify_scheduler.operations.gate_library.Reset).
The `reset` instruction can be used to set the state of the qubit to the $|0\rangle$ state, similar to the effect of the
`init` instruction.
4. [Single gate multi qubit (SGMQ)](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/single-gate-multiple-qubit-notation.html)
notation is unpacked; the gate is applied to each qubit on a separate line.
5. Control instructions ([`barrier`](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/control_instructions/barrier_instruction.html)
and [`wait`](https://qutech-delft.github.io/cQASM-spec/latest/language_specification/statements/instructions/control_instructions/wait_instruction.html))
are currently not supported.
_**Note**: processing of the control instructions is currently under active development, but not yet part of the latest
version of OpenSquirrel._
6. Angles are translated from radians to degrees.

!!! warning "Unsupported gates"

    The quantify-scheduler exporter does not support the [Rn gate](https://qutech-delft.github.io/cQASM-spec/latest/standard_gate_set/single_qubit/sq_Rn.html)
    in general.
    Unless both the $n_x$ and $n_y$ components are zero, or just the $n_z$ component is zero, it will raise an error
    (`UnSupportedGateError`) if this gate is part of the circuit that is to be exported.

    The same error is raised if the circuit to be exported contains a Hadamard, SWAP, or any arbitrary two-qubit gate
    that is not either a CNOT or CZ gate.
    [Decomposition passes](../decomposition/index.md) can be used to decompose the circuit to gates that the
    quantify-scheduler exporter supports.

The four examples below show how circuits written in [cQASM](https://qutech-delft.github.io/cQASM-spec/) are exported to a quantify-scheduler
[`Schedule`](https://quantify-os.org/docs/quantify-scheduler/v0.25.0/autoapi/quantify_scheduler/index.html#quantify_scheduler.Schedule).

!!! example ""

    === "Simple circuit"

        ```python
        from opensquirrel import Circuit
        from opensquirrel.passes.exporter import ExportFormat
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

        exported_schedule, bitstring_mapping = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)

        for schedulable in exported_schedule.schedulables.values():
            print(exported_schedule.operations[schedulable["operation_id"]].name)
        print('\n', "bitstring mapping: ", bitstring_mapping)
        ```

        ```
        Rxy(90, 90, 'q[0]')
        Rxy(180, 0, 'q[0]')
        CNOT (q[0], q[1])
        Measure q[0]
        Measure q[1]

        bitstring mapping:  [(0, 0), (0, 1)]
        ```

        Note that the bit register declaration and assignment to bit variables have been discarded (2.),
        the SGMQ notation has been unpacked (4.), and the angles have been translated from radians to degrees (6.).
        _The numbers refer to the differences listed above._

        According to the description of the _bitstring mapping_ above, note that the outcome of the first measurement on
        qubit at index $0$, $(i,j) = (0,0)$, is mapped to the (virtual) bit variable ($k=0$; the first ordered pair),
        and the outcome of the first measurement on qubit at index $1$, $(i,j) = (0,1)$, is mapped to the (virtual) bit
        variable ($k=1$; the second ordered pair).

    === "Registers"

        ```python
        from opensquirrel import Circuit
        from opensquirrel.passes.exporter import ExportFormat
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

        exported_circuit = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        for schedulable in exported_schedule.schedulables.values():
            print(exported_schedule.operations[schedulable["operation_id"]].name)
        print('\n', "bitstring mapping: ", bitstring_mapping)
        ```

        ```
        Rxy(90, 90, 'q[0]')
        Rxy(180, 0, 'q[0]')
        CNOT (q[0], q[1])
        Measure q[0]
        Measure q[1]
        Rxy(90, 90, 'q[3]')
        Rxy(180, 0, 'q[3]')
        CNOT (q[3], q[1])
        Measure q[3]
        Measure q[1]

        bitstring mapping:  [(None, None), (0, 0), (0, 1), (0, 3), (1, 1)]
        ```

        Note that all qubit register declarations are combined into a single (virtual) qubit register (1.), the bit
        register declaration and assignment to bit variables have been discarded (2.), the SGMQ notation has been
        unpacked (4.), and the angles have been translated from radians to degrees (6.).
        _The numbers refer to the differences listed above._

        In particular, this example illustrates that all qubit registers have been combined into a single (virtual)
        qubit register `q`, _i.e._, the registers `qA` and `qB` have been concatenated into `q`,
        such that `qA[0], qA[1] = q[0], q[1]` and `qB[0], qB[1], qB[2] = q[2], q[3], q[4]`.
        The qubit registers are concatenated in the order they are declared.

        Moreover, even though the bit registers have been discarded in the circuit, the mapping from meausurement to
        (virtual) bit variable has been stored in the _bitstring mapping_.
        Note that, just like with the translation of the qubit register declarations to the single virtual register `q`,
        the bit register declarations are also concatenated in the order they are declared into a single bit register
        `b`.
        In this example, the virtual bit register translation is as follows: `bA[0], bA[1], bA[2] = b[0], b[1], b[2]`
        and `bB[0], bB[1] = b[3], b[4]`.
        Accodingly, the $k$-th element in the bitstring mapping corresponds to the $k$-th element of the bit register.

        For instance, the statement `bB[1] = measure qA[1]` in the original circuit becomes, in terms of virtual
        registers, `b[4] = measure q[1]`.
        Since this is the second measurement on `q[1]`, the acquisition index is $i = 1$ (counting starts at $0$) and
        the qubit index is $j = 1$, such that the measurement is given by the ordered pair $(1, 1)$.
        Because the outcome of this measurement is stored in `b[4]`,
        the ordered pair is at index $4$ in the bitregister mapping.


    === "`init` and `reset`"

        ```python
        from opensquirrel import Circuit
        from opensquirrel.passes.exporter import ExportFormat
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

        exported_circuit = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        for schedulable in exported_schedule.schedulables.values():
            print(exported_schedule.operations[schedulable["operation_id"]].name)
        print('\n', "bitstring mapping: ", bitstring_mapping)
        ```

        ```
        Rxy(90, 90, 'q[0]')
        Rxy(180, 0, 'q[0]')
        CNOT (q[0], q[1])
        Measure q[0]
        Measure q[1]
        Reset q[0]
        Reset q[1]
        Rxy(90, 90, 'q[0]')
        Rxy(180, 0, 'q[0]')
        Rz(180, 'q[0]')
        CNOT (q[0], q[1])
        Measure q[0]
        Measure q[1]

        bitstring mapping:  [(1, 0), (1, 1)]
        ```

        Note that the bit register declaration and assignment to bit variables have been discarded (2.),
        the `init` instructions have been ignored and the `reset` instructions have been translated to [Reset](https://quantify-os.org/docs/quantify-scheduler/v0.25.0/autoapi/quantify_scheduler/operations/gate_library/index.html#quantify_scheduler.operations.gate_library.Reset),
        the SGMQ notation has been unpacked (4.), and the angles have been translated from radians to degrees (6.).
        _The numbers refer to the differences listed above._

        The [quantify-scheduler operation library](https://quantify-os.org/docs/quantify-scheduler/v0.25.0/autoapi/quantify_scheduler/operations/gate_library/index.html)
        does not distinguish between an `init` and a `reset` instruction.
        For now, the `init` instruction is ignored and the `reset` instruction is translated to
        [Reset](https://quantify-os.org/docs/quantify-scheduler/v0.25.0/autoapi/quantify_scheduler/operations/gate_library/index.html#quantify_scheduler.operations.gate_library.Reset).
        Note that one can us the `reset` instruction to set the state of the qubit to the $|0\rangle$ state,
        which is similar to the effect of the `init` instruction.

!!! warning "macOS ARM not supported"

    The quantify-scheduler exporter cannot run on macOS ARM, due to the fact that the required dependency
    `pyqt5-qt5==5.15.2` does provide binaries for that architecture.
