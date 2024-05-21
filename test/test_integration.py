# This integration test also serves as example and code documentation.

import importlib.util
import unittest

from opensquirrel.circuit import Circuit
from opensquirrel.decomposer.cnot_decomposer import CNOTDecomposer
from opensquirrel.decomposer.mckay_decomposer import McKayDecomposer
from opensquirrel.decomposer.zyz_decomposer import ZYZDecomposer
from opensquirrel.default_gates import *
from opensquirrel.exporter.export_format import ExportFormat


class IntegrationTest(unittest.TestCase):
    def test_simple(self):
        circuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] q

                Ry(1.23) q[0]
                Ry(2.34) q[1]
                CNOT q[0], q[1]
                Rx(-2.3) q[0]
                Ry(-3.14) q[1]
            """
        )

        #    Decompose CNOT as
        #
        #    -----•-----        ------- Z -------
        #         |        ==           |
        #    -----⊕----         --- H --•-- H ---
        #

        circuit.replace(
            CNOT,
            lambda control, target: [
                H(target),
                CZ(control, target),
                H(target),
            ],
        )

        # Do 1q-gate fusion and decomposer with McKay decomposition.
        circuit.merge_single_qubit_gates()
        circuit.decompose(decomposer=McKayDecomposer)

        # Write the transformed circuit as a cQasm3 string.
        self.assertEqual(
            str(circuit),
            """version 3.0

qubit[3] q

Rz(3.1415927) q[0]
X90 q[0]
Rz(1.9115927) q[0]
X90 q[0]
Rz(3.1415927) q[1]
X90 q[1]
Rz(2.372389) q[1]
X90 q[1]
Rz(3.1415927) q[1]
CZ q[0], q[1]
Rz(1.5707963) q[0]
X90 q[0]
Rz(0.84159265) q[0]
X90 q[0]
Rz(1.5707963) q[0]
Rz(3.1415927) q[1]
X90 q[1]
Rz(1.572389) q[1]
X90 q[1]
Rz(3.1415927) q[1]
""",
        )

    def test_measurement(self):
        circuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] q
                bit[3] b

                Ry(2.34) q[2]
                Rz(1.5707963) q[0]
                Ry(-0.2) q[0]
                CNOT q[1], q[0]
                Rz(1.5789) q[0]
                CNOT q[1], q[0]
                Rz(2.5707963) q[1]
                b[0, 2] = measure q[0,2]
            """,
        )
        circuit.merge_single_qubit_gates()
        circuit.decompose(decomposer=McKayDecomposer)
        self.assertEqual(
            str(circuit),
            """version 3.0

qubit[3] q

Rz(1.5707963) q[0]
X90 q[0]
Rz(2.9415927) q[0]
X90 q[0]
Rz(3.1415927) q[0]
CNOT q[1], q[0]
Rz(-2.3521427) q[0]
X90 q[0]
Rz(3.1415927) q[0]
X90 q[0]
Rz(0.78945) q[0]
CNOT q[1], q[0]
Rz(3.1415927) q[2]
X90 q[2]
Rz(0.80159265) q[2]
X90 q[2]
Rz(-1.8561945) q[1]
X90 q[1]
Rz(3.1415927) q[1]
X90 q[1]
Rz(1.2853981) q[1]
measure q[0]
measure q[2]
""",
        )

    def test_consecutive_measurements(self):
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[3] q
            bit[3] b

            H q[0]
            H q[1]
            H q[2]
            b[0] = measure q[0]
            b[1] = measure q[1]
            b[2] = measure q[2]
            """
        )
        circuit.merge_single_qubit_gates()
        circuit.decompose(decomposer=McKayDecomposer)
        self.assertEqual(
            str(circuit),
            """version 3.0

qubit[3] q

X90 q[0]
Rz(1.5707963) q[0]
X90 q[0]
X90 q[1]
Rz(1.5707963) q[1]
X90 q[1]
X90 q[2]
Rz(1.5707963) q[2]
X90 q[2]
measure q[0]
measure q[1]
measure q[2]
""",
        )

    def test_measure_order(self):
        circuit = Circuit.from_string(
            """
                version 3.0

                qubit[2] q
                bit[2] b

                Rz(-2.3561945) q[1]
                Rz(1.5707963) q[1]
                b[1, 0] = measure q[1,0]
            """
        )
        circuit.merge_single_qubit_gates()
        circuit.decompose(decomposer=McKayDecomposer)
        self.assertEqual(
            str(circuit),
            """version 3.0

qubit[2] q

Rz(2.7488936) q[1]
X90 q[1]
Rz(3.1415927) q[1]
X90 q[1]
Rz(-0.3926991) q[1]
measure q[1]
measure q[0]
""",
        )

    def test_qi(self):
        circuit = Circuit.from_string(
            """
            version 3.0

            // This is a single line comment which ends on the newline.
            // The cQASM string must begin with the version instruction (apart from any preceding comments).

            /* This is a multi-
            line comment block */

            qubit[4] q   // Qubit (register) declaration

            // Let us create a Bell state on 2 qubits and a |+> state on the third qubit

            H q[2]
            H q[1]
            H q[0]
            Rz(1.5707963) q[0]
            Ry(-0.2) q[0]
            CNOT q[1], q[0]
            Rz(1.5789) q[0]
            CNOT q[1], q[0]
            CNOT q[1], q[2]
            Rz(2.5707963) q[1]
            CR(2.123) q[2], q[3]
            Ry(-1.5707963) q[1]
            """
        )

        circuit.merge_single_qubit_gates()
        circuit.decompose(decomposer=McKayDecomposer)

        self.assertEqual(
            str(circuit),
            """version 3.0

qubit[4] q

X90 q[1]
Rz(1.5707963) q[1]
X90 q[1]
Rz(-0.2) q[0]
X90 q[0]
Rz(1.5707963) q[0]
X90 q[0]
Rz(1.5707963) q[0]
CNOT q[1], q[0]
Rz(-2.3521427) q[0]
X90 q[0]
Rz(3.1415927) q[0]
X90 q[0]
Rz(0.78945) q[0]
CNOT q[1], q[0]
X90 q[2]
Rz(1.5707963) q[2]
X90 q[2]
CNOT q[1], q[2]
CR(2.123) q[2], q[3]
Rz(2.5707963) q[1]
X90 q[1]
Rz(1.5707964) q[1]
X90 q[1]
Rz(3.1415927) q[1]
""",
        )

    def test_libqasm_error(self):
        with self.assertRaisesRegex(
            Exception,
            r"Parsing error: Error at <unknown file name>:4:17\.\.19: failed to resolve instruction 'Ry' with argument pack \(qubit, float, int\)",
        ):
            Circuit.from_string(
                """
                version 3.0
                qubit[3] q
                Ry q[0], 1.23, 1
                """,
            )

    def test_export_quantify_scheduler(self):
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[3] q
            bit[3] b

            H q[1]
            CZ q[0], q[1]
            CNOT q[0], q[1]
            CRk(4) q[0], q[1]
            H q[0]
            b[0:1] = measure q[0:1]
            """
        )

        circuit.decompose(decomposer=CNOTDecomposer)

        # Quantify-scheduler prefers CZ.
        circuit.replace(
            CNOT,
            lambda control, target: [
                H(target),
                CZ(control, target),
                H(target),
            ],
        )

        # Reduce gate count by single-qubit gate fusion.
        circuit.merge_single_qubit_gates()

        # FIXME: for best gate count we need a Z-XY decomposer.
        # See https://github.com/QuTech-Delft/OpenSquirrel/issues/98
        circuit.decompose(decomposer=ZYZDecomposer)

        if importlib.util.find_spec("quantify_scheduler") is None:
            with self.assertRaisesRegex(
                Exception, "quantify-scheduler is not installed, or cannot be installed on " "your system"
            ):
                circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        else:
            exported_schedule = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)

            self.assertEqual(exported_schedule.name, "Exported OpenSquirrel circuit")

            operations = [
                exported_schedule.operations[schedulable["operation_id"]].name
                for schedulable in exported_schedule.schedulables.values()
            ]

            self.assertEqual(
                operations,
                [
                    "Rz(-180, 'q[1]')",
                    "Rxy(90, 90, 'q[1]')",
                    "CZ (q[0], q[1])",
                    "Rz(-180, 'q[1]')",
                    "Rxy(90, 90, 'q[1]')",
                    "CZ (q[0], q[1])",
                    "Rz(90, 'q[1]')",
                    "Rxy(11.25, 90, 'q[1]')",
                    "Rz(-90, 'q[1]')",
                    "CZ (q[0], q[1])",
                    "Rz(90, 'q[1]')",
                    "Rxy(-11.25, 90, 'q[1]')",
                    "Rz(-90, 'q[1]')",
                    "CZ (q[0], q[1])",
                    "Rz(11.25, 'q[0]')",
                    "Rxy(-90, 90, 'q[0]')",
                    "Rz(-180, 'q[0]')",
                    "Rz(-180, 'q[1]')",
                    "Rxy(90, 90, 'q[1]')",
                    "Measure q[0]",
                    "Measure q[1]",
                ],
            )


if __name__ == "__main__":
    unittest.main()
