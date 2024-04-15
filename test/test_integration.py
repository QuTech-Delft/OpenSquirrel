# This integration test also serves as example and code documentation.

import importlib.util
import unittest

from opensquirrel.circuit import Circuit
from opensquirrel.cnot_decomposer import CNOTDecomposer
from opensquirrel.default_gates import *
from opensquirrel.export_format import ExportFormat
from opensquirrel.mckay_decomposer import McKayDecomposer
from opensquirrel.zyz_decomposer import ZYZDecomposer


class IntegrationTest(unittest.TestCase):
    def test_simple(self):
        myCircuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] qreg

                Ry qreg[0], 1.23
                Ry qreg[1], 2.34
                CNOT qreg[0], qreg[1]
                Rx qreg[0], -2.3
                Ry qreg[1], -3.14
            """
        )

        #    Decompose CNOT as
        #
        #    -----•-----        ------- Z -------
        #         |        ==           |
        #    -----⊕----        --- H --•-- H ---
        #

        myCircuit.replace(
            CNOT,
            lambda control, target: [
                H(target),
                CZ(control, target),
                H(target),
            ],
        )

        # Do 1q-gate fusion and decompose with McKay decomposition.

        myCircuit.merge_single_qubit_gates()

        myCircuit.decompose(decomposer=McKayDecomposer)

        # Write the transformed circuit as a cQasm3 string.

        output = str(myCircuit)

        self.assertEqual(
            output,
            """version 3.0

qubit[3] qreg

Rz qreg[0], 3.1415927
X90 qreg[0]
Rz qreg[0], 1.9115927
X90 qreg[0]
Rz qreg[1], 3.1415927
X90 qreg[1]
Rz qreg[1], 2.372389
X90 qreg[1]
Rz qreg[1], 3.1415927
CZ qreg[0], qreg[1]
Rz qreg[0], 1.5707963
X90 qreg[0]
Rz qreg[0], 0.84159265
X90 qreg[0]
Rz qreg[0], 1.5707963
Rz qreg[1], 3.1415927
X90 qreg[1]
Rz qreg[1], 1.572389
X90 qreg[1]
Rz qreg[1], 3.1415927
""",
        )

    def test_measurement(self):
        myCircuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] qreg

                Ry qreg[2], 2.34
                Rz qreg[0], 1.5707963
                Ry qreg[0], -0.2
                CNOT qreg[1], qreg[0]
                Rz qreg[0], 1.5789
                CNOT qreg[1], qreg[0]
                Rz qreg[1], 2.5707963
                measure qreg[0,2]
            """,
            use_libqasm=True,
        )
        myCircuit.merge_single_qubit_gates()
        myCircuit.decompose(decomposer=McKayDecomposer)
        self.assertEqual(
            str(myCircuit),
            """version 3.0

qubit[3] qreg

Rz qreg[0], 1.5707963
X90 qreg[0]
Rz qreg[0], 2.9415927
X90 qreg[0]
Rz qreg[0], 3.1415927
CNOT qreg[1], qreg[0]
Rz qreg[0], -2.3521427
X90 qreg[0]
Rz qreg[0], 3.1415927
X90 qreg[0]
Rz qreg[0], 0.78945
CNOT qreg[1], qreg[0]
Rz qreg[2], 3.1415927
X90 qreg[2]
Rz qreg[2], 0.80159265
X90 qreg[2]
Rz qreg[1], -1.8561945
X90 qreg[1]
Rz qreg[1], 3.1415927
X90 qreg[1]
Rz qreg[1], 1.2853981
measure qreg[0]
measure qreg[2]
""",
        )

    def test_consecutive_measurements(self):
        myCircuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] qreg

                H qreg[0]
                H qreg[1]
                H qreg[2]
                measure qreg[0]
                measure qreg[1]
                measure qreg[2]
            """
        )
        myCircuit.merge_single_qubit_gates()
        myCircuit.decompose(decomposer=McKayDecomposer)
        self.assertEqual(
            str(myCircuit),
            """version 3.0

qubit[3] qreg

X90 qreg[0]
Rz qreg[0], 1.5707963
X90 qreg[0]
X90 qreg[1]
Rz qreg[1], 1.5707963
X90 qreg[1]
X90 qreg[2]
Rz qreg[2], 1.5707963
X90 qreg[2]
measure qreg[0]
measure qreg[1]
measure qreg[2]
""",
        )

    def test_measure_order(self):
        myCircuit = Circuit.from_string(
            """
                version 3.0

                qubit[2] qreg

                Rz qreg[1], -2.3561945
                Rz qreg[1], 1.5707963
                measure qreg[1,0]
            """
        )
        myCircuit.merge_single_qubit_gates()
        myCircuit.decompose(decomposer=McKayDecomposer)
        output = str(myCircuit)
        expected = """version 3.0

qubit[2] qreg

Rz qreg[1], 2.7488936
X90 qreg[1]
Rz qreg[1], 3.1415927
X90 qreg[1]
Rz qreg[1], -0.3926991
measure qreg[1]
measure qreg[0]
"""
        self.assertEqual(output, expected)

    def test_qi(self):
        myCircuit = Circuit.from_string(
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

        myCircuit.merge_single_qubit_gates()

        myCircuit.decompose(decomposer=McKayDecomposer)
        output = str(myCircuit)

        expected = """version 3.0

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
"""

        self.assertEqual(output, expected)

    def test_libqasm_error(self):
        with self.assertRaisesRegex(
            Exception,
            r"Parsing error: Error at <unknown file name>:4:21\.\.23: failed to resolve instruction 'Ry' with argument pack \(qubit, float, int\)",
        ):
            Circuit.from_string(
                """
                    version 3.0
                    qubit[3] qreg
                    Ry qreg[0], 1.23, 1
                """,
                use_libqasm=True,
            )

    def test_export_quantify_scheduler(self):
        myCircuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] qreg

                H qreg[1]
                CZ qreg[0], qreg[1]
                CNOT qreg[0], qreg[1]
                CRk qreg[0], qreg[1], 4
                H qreg[0]
            """
        )

        myCircuit.decompose(decomposer=CNOTDecomposer)

        # Quantify-scheduler prefers CZ.
        myCircuit.replace(
            CNOT,
            lambda control, target: [
                H(target),
                CZ(control, target),
                H(target),
            ],
        )

        # Reduce gate count by single-qubit gate fusion.
        myCircuit.merge_single_qubit_gates()

        # FIXME: for best gate count we need a Z-XY decomposer.
        # See https://github.com/QuTech-Delft/OpenSquirrel/issues/98
        myCircuit.decompose(decomposer=ZYZDecomposer)

        if importlib.util.find_spec("quantify_scheduler") is None:
            with self.assertRaisesRegex(
                Exception, "quantify-scheduler is not installed, or cannot be installed on " "your system"
            ):
                myCircuit.export(format=ExportFormat.QUANTIFY_SCHEDULER)
        else:
            exported_schedule = myCircuit.export(format=ExportFormat.QUANTIFY_SCHEDULER)

            self.assertEqual(exported_schedule.name, "Exported OpenSquirrel circuit")

            operations = [
                exported_schedule.operations[schedulable["operation_id"]].name
                for schedulable in exported_schedule.schedulables.values()
            ]

            self.assertEqual(
                operations,
                [
                    "Rz(3.1415927, 'qreg[1]')",
                    "Rxy(1.5707963, 1.5707963, 'qreg[1]')",
                    "CZ (qreg[0], qreg[1])",
                    "Rz(3.1415927, 'qreg[1]')",
                    "Rxy(1.5707963, 1.5707963, 'qreg[1]')",
                    "CZ (qreg[0], qreg[1])",
                    "Rz(1.5707963, 'qreg[1]')",
                    "Rxy(0.19634954, 1.5707963, 'qreg[1]')",
                    "Rz(-1.5707963, 'qreg[1]')",
                    "CZ (qreg[0], qreg[1])",
                    "Rz(1.5707963, 'qreg[1]')",
                    "Rxy(-0.19634954, 1.5707963, 'qreg[1]')",
                    "Rz(-1.5707963, 'qreg[1]')",
                    "CZ (qreg[0], qreg[1])",
                    "Rz(0.19634954, 'qreg[0]')",
                    "Rxy(-1.5707963, 1.5707963, 'qreg[0]')",
                    "Rz(3.1415927, 'qreg[0]')",
                    "Rz(3.1415927, 'qreg[1]')",
                    "Rxy(1.5707963, 1.5707963, 'qreg[1]')",
                ],
            )


if __name__ == "__main__":
    unittest.main()
