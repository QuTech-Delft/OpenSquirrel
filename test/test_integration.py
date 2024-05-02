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

                Ry q[0], 1.23
                Ry q[1], 2.34
                CNOT q[0], q[1]
                Rx q[0], -2.3
                Ry q[1], -3.14
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

Rz q[0], 3.1415927
X90 q[0]
Rz q[0], 1.9115927
X90 q[0]
Rz q[1], 3.1415927
X90 q[1]
Rz q[1], 2.372389
X90 q[1]
Rz q[1], 3.1415927
CZ q[0], q[1]
Rz q[0], 1.5707963
X90 q[0]
Rz q[0], 0.84159265
X90 q[0]
Rz q[0], 1.5707963
Rz q[1], 3.1415927
X90 q[1]
Rz q[1], 1.572389
X90 q[1]
Rz q[1], 3.1415927
""",
        )

    def test_measurement(self):
        circuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] q

                Ry q[2], 2.34
                Rz q[0], 1.5707963
                Ry q[0], -0.2
                CNOT q[1], q[0]
                Rz q[0], 1.5789
                CNOT q[1], q[0]
                Rz q[1], 2.5707963
                measure q[0,2]
            """,
        )
        circuit.merge_single_qubit_gates()
        circuit.decompose(decomposer=McKayDecomposer)
        self.assertEqual(
            str(circuit),
            """version 3.0

qubit[3] q

Rz q[0], 1.5707963
X90 q[0]
Rz q[0], 2.9415927
X90 q[0]
Rz q[0], 3.1415927
CNOT q[1], q[0]
Rz q[0], -2.3521427
X90 q[0]
Rz q[0], 3.1415927
X90 q[0]
Rz q[0], 0.78945
CNOT q[1], q[0]
Rz q[2], 3.1415927
X90 q[2]
Rz q[2], 0.80159265
X90 q[2]
Rz q[1], -1.8561945
X90 q[1]
Rz q[1], 3.1415927
X90 q[1]
Rz q[1], 1.2853981
measure q[0]
measure q[2]
""",
        )

    def test_consecutive_measurements(self):
        circuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] q

                H q[0]
                H q[1]
                H q[2]
                measure q[0]
                measure q[1]
                measure q[2]
            """
        )
        circuit.merge_single_qubit_gates()
        circuit.decompose(decomposer=McKayDecomposer)
        self.assertEqual(
            str(circuit),
            """version 3.0

qubit[3] q

X90 q[0]
Rz q[0], 1.5707963
X90 q[0]
X90 q[1]
Rz q[1], 1.5707963
X90 q[1]
X90 q[2]
Rz q[2], 1.5707963
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

                Rz q[1], -2.3561945
                Rz q[1], 1.5707963
                measure q[1,0]
            """
        )
        circuit.merge_single_qubit_gates()
        circuit.decompose(decomposer=McKayDecomposer)
        self.assertEqual(
            str(circuit),
            """version 3.0

qubit[2] q

Rz q[1], 2.7488936
X90 q[1]
Rz q[1], 3.1415927
X90 q[1]
Rz q[1], -0.3926991
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
            Rz q[0], 1.5707963
            Ry q[0], -0.2
            CNOT q[1], q[0]
            Rz q[0], 1.5789
            CNOT q[1], q[0]
            CNOT q[1], q[2]
            Rz q[1], 2.5707963
            CR q[2], q[3], 2.123
            Ry q[1], -1.5707963
            """
        )

        circuit.merge_single_qubit_gates()
        circuit.decompose(decomposer=McKayDecomposer)

        self.assertEqual(
            str(circuit),
            """version 3.0

qubit[4] q

X90 q[1]
Rz q[1], 1.5707963
X90 q[1]
Rz q[0], -0.2
X90 q[0]
Rz q[0], 1.5707963
X90 q[0]
Rz q[0], 1.5707963
CNOT q[1], q[0]
Rz q[0], -2.3521427
X90 q[0]
Rz q[0], 3.1415927
X90 q[0]
Rz q[0], 0.78945
CNOT q[1], q[0]
X90 q[2]
Rz q[2], 1.5707963
X90 q[2]
CNOT q[1], q[2]
CR q[2], q[3], 2.123
Rz q[1], 2.5707963
X90 q[1]
Rz q[1], 1.5707964
X90 q[1]
Rz q[1], 3.1415927
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

            H q[1]
            CZ q[0], q[1]
            CNOT q[0], q[1]
            CRk q[0], q[1], 4
            H q[0]
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
                ],
            )


if __name__ == "__main__":
    unittest.main()
