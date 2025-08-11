from opensquirrel import Circuit
from opensquirrel.passes.exporter import ExportFormat


class TestCqasmV1Exporter:

    def test_simple_circuit(self) -> None:
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[2] q
            bit[2] b

            H q[0]
            CNOT q[0], q[1]
            b = measure q
            """,
        )
        exported_circuit = circuit.export(fmt=ExportFormat.CQASM_V1)
        assert (
            str(exported_circuit)
            == """version 1.0

qubits 2

h q[0]
cnot q[0], q[1]
measure_z q[0]
measure_z q[1]
"""
        )

    def test_registers(self) -> None:
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
            """,
        )
        exported_circuit = circuit.export(fmt=ExportFormat.CQASM_V1)
        assert (
            str(exported_circuit)
            == """version 1.0

qubits 5

h q[0]
cnot q[0], q[1]
measure_z q[0]
measure_z q[1]
h q[3]
cnot q[3], q[1]
measure_z q[3]
measure_z q[1]
"""
        )

    def test_init_and_reset(self) -> None:
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
            """,
        )
        exported_circuit = circuit.export(fmt=ExportFormat.CQASM_V1)
        assert (
            str(exported_circuit)
            == """version 1.0

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
"""
        )

    def test_sgmq_notation_and_uniform_barriers(self) -> None:
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
            """,
        )
        exported_circuit = circuit.export(fmt=ExportFormat.CQASM_V1)
        assert (
            str(exported_circuit)
            == """version 1.0

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
"""
        )


class TestQuantifySchedulerExporter:

    def test_simple_circuit(self) -> None:
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[2] q
            bit[2] b

            Ry(pi/2) q[0]
            X q[0]
            CNOT q[0], q[1]
            b = measure q
            """,
        )
        exported_schedule, bitstring_mapping = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        operations = [exported_schedule.operations[schedulable["operation_id"]].name for schedulable in
                      exported_schedule.schedulables.values()]

        assert operations == [
            "Rxy(90, 90, 'q[0]')",
            "Rxy(180, 0, 'q[0]')",
            'CNOT (q[0], q[1])',
            'Measure q[0]',
            'Measure q[1]'
        ]
        assert bitstring_mapping == [(0, 0), (0, 1)]

    def test_registers(self) -> None:
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[2] qA
            bit[3] bA

            Ry(pi/2) qA[0]
            X qA[0]
            CNOT qA[0], qA[1]

            bA[1,2] = measure qA

            qubit[3] qB
            bit[2] bB

            Ry(pi/2) qB[1]
            X qB[1]
            CNOT qB[1], qA[1]

            bB[0] = measure qB[1]
            bB[1] = measure qA[1]
            """,
        )
        exported_schedule, bitstring_mapping = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        operations = [exported_schedule.operations[schedulable["operation_id"]].name for schedulable in
                      exported_schedule.schedulables.values()]

        assert operations == [
            "Rxy(90, 90, 'q[0]')",
            "Rxy(180, 0, 'q[0]')",
            'CNOT (q[0], q[1])',
            'Measure q[0]',
            'Measure q[1]',
            "Rxy(90, 90, 'q[3]')",
            "Rxy(180, 0, 'q[3]')",
            'CNOT (q[3], q[1])',
            'Measure q[3]',
            'Measure q[1]'
        ]
        assert bitstring_mapping == [(None, None), (0, 0), (0, 1), (0, 3), (1, 1)]

    def test_init_and_reset(self) -> None:
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[2] q
            bit[2] b

            init q

            Ry(pi/2) q[0]
            X q[0]
            CNOT q[0], q[1]
            b = measure q

            reset q

            Ry(pi/2) q[0]
            X q[0]
            Z q[0]
            CNOT q[0], q[1]
            b = measure q
            """,
        )
        exported_schedule, bitstring_mapping = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        operations = [exported_schedule.operations[schedulable["operation_id"]].name for schedulable in
                      exported_schedule.schedulables.values()]

        assert operations == [
            "Rxy(90, 90, 'q[0]')",
            "Rxy(180, 0, 'q[0]')",
            'CNOT (q[0], q[1])',
            'Measure q[0]',
            'Measure q[1]',
            'Reset q[0]',
            'Reset q[1]',
            "Rxy(90, 90, 'q[0]')",
            "Rxy(180, 0, 'q[0]')",
            "Rz(180, 'q[0]')",
            'CNOT (q[0], q[1])',
            'Measure q[0]',
            'Measure q[1]'
        ]
        assert bitstring_mapping == [(1, 0), (1, 1)]
