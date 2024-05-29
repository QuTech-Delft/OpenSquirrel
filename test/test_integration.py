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
        myCircuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] qreg

                Ry(1.23) qreg[0]
                Ry(2.34) qreg[1]
                CNOT qreg[0], qreg[1]
                Rx(-2.3) qreg[0]
                Ry(-3.14) qreg[1]
            """
        )

        #    Decompose CNOT as
        #
        #    -----•-----        ------- Z -------
        #         |        ==           |
        #    -----⊕----         --- H --•-- H ---
        #

        myCircuit.replace(
            CNOT,
            lambda control, target: [
                H(target),
                CZ(control, target),
                H(target),
            ],
        )

        # Do 1q-gate fusion and decomposer with McKay decomposition.

        myCircuit.merge_single_qubit_gates()

        myCircuit.decompose(decomposer=McKayDecomposer)

        # Write the transformed circuit as a cQasm3 string.

        output = str(myCircuit)
        self.assertEqual(
            output,
            """version 3.0

qubit[3] qreg

Rz(3.1415927) qreg[0]
X90 qreg[0]
Rz(1.9115927) qreg[0]
X90 qreg[0]
Rz(3.1415927) qreg[1]
X90 qreg[1]
Rz(2.372389) qreg[1]
X90 qreg[1]
Rz(3.1415927) qreg[1]
CZ qreg[0], qreg[1]
Rz(1.5707963) qreg[0]
X90 qreg[0]
Rz(0.84159265) qreg[0]
X90 qreg[0]
Rz(1.5707963) qreg[0]
Rz(3.1415927) qreg[1]
X90 qreg[1]
Rz(1.5723889) qreg[1]
X90 qreg[1]
Rz(3.1415927) qreg[1]
""",
        )

    def test_measurement(self):
        myCircuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] qreg

                Ry(2.34) qreg[2]
                Rz(1.5707963) qreg[0]
                Ry(-0.2) qreg[0]
                CNOT qreg[1], qreg[0]
                Rz(1.5789) qreg[0]
                CNOT qreg[1], qreg[0]
                Rz(2.5707963) qreg[1]
                measure qreg[0,2]
            """,
        )
        myCircuit.merge_single_qubit_gates()
        myCircuit.decompose(decomposer=McKayDecomposer)
        self.assertEqual(
            str(myCircuit),
            """version 3.0

qubit[3] qreg

Rz(1.5707963) qreg[0]
X90 qreg[0]
Rz(2.9415927) qreg[0]
X90 qreg[0]
Rz(3.1415926) qreg[0]
CNOT qreg[1], qreg[0]
Rz(1.5789) qreg[0]
CNOT qreg[1], qreg[0]
Rz(3.1415927) qreg[2]
X90 qreg[2]
Rz(0.80159265) qreg[2]
X90 qreg[2]
Rz(2.5707963) qreg[1]
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
Rz(1.5707963) qreg[0]
X90 qreg[0]
X90 qreg[1]
Rz(1.5707963) qreg[1]
X90 qreg[1]
X90 qreg[2]
Rz(1.5707963) qreg[2]
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

                Rz(-2.3561945) qreg[1]
                Rz(1.5707963) qreg[1]
                measure qreg[1,0]
            """
        )
        myCircuit.merge_single_qubit_gates()
        myCircuit.decompose(decomposer=McKayDecomposer)
        output = str(myCircuit)
        expected = """version 3.0

qubit[2] qreg

Rz(2.7488936) qreg[1]
X90 qreg[1]
Rz(3.1415927) qreg[1]
X90 qreg[1]
Rz(-0.3926991) qreg[1]
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

        myCircuit.merge_single_qubit_gates()

        myCircuit.decompose(decomposer=McKayDecomposer)
        output = str(myCircuit)
        expected = """version 3.0

qubit[4] q

X90 q[1]
Rz(1.5707963) q[1]
X90 q[1]
Rz(-0.20000005) q[0]
X90 q[0]
Rz(1.5707963) q[0]
X90 q[0]
Rz(1.5707963) q[0]
CNOT q[1], q[0]
Rz(1.5789) q[0]
CNOT q[1], q[0]
X90 q[2]
Rz(1.5707963) q[2]
X90 q[2]
CNOT q[1], q[2]
CR(2.123) q[2], q[3]
Rz(2.5707962) q[1]
X90 q[1]
Rz(1.5707963) q[1]
X90 q[1]
Rz(3.1415927) q[1]
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
            )

    def test_export_quantify_scheduler(self):
        myCircuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] qreg

                H qreg[1]
                CZ qreg[0], qreg[1]
                CNOT qreg[0], qreg[1]
                CRk(4) qreg[0], qreg[1]
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
                myCircuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
        else:
            exported_schedule = myCircuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)

            self.assertEqual(exported_schedule.name, "Exported OpenSquirrel circuit")

            operations = [
                exported_schedule.operations[schedulable["operation_id"]].name
                for schedulable in exported_schedule.schedulables.values()
            ]

            self.assertEqual(
                operations,
                [
                    "Rz(-180, 'qreg[1]')",
                    "Rxy(90, 90, 'qreg[1]')",
                    "CZ (qreg[0], qreg[1])",
                    "Rz(-180, 'qreg[1]')",
                    "Rxy(90, 90, 'qreg[1]')",
                    "CZ (qreg[0], qreg[1])",
                    "Rz(90, 'qreg[1]')",
                    "Rxy(11.25, 90, 'qreg[1]')",
                    "Rz(-90, 'qreg[1]')",
                    "CZ (qreg[0], qreg[1])",
                    "Rz(90, 'qreg[1]')",
                    "Rxy(-11.25, 90, 'qreg[1]')",
                    "Rz(-90, 'qreg[1]')",
                    "CZ (qreg[0], qreg[1])",
                    "Rz(11.25, 'qreg[0]')",
                    "Rxy(-90, 90, 'qreg[0]')",
                    "Rz(-180, 'qreg[0]')",
                    "Rz(-180, 'qreg[1]')",
                    "Rxy(90, 90, 'qreg[1]')",
                ],
            )

    def test_H_identity_integration(self):
        myCircuit = Circuit.from_string(
            """
            version 3.0

            qubit[1] q   // Qubit (register) declaration

            Y90 q[0]
            X q[0]
            """
        )
        myCircuit.merge_single_qubit_gates()
        output = str(myCircuit)
        expected = """version 3.0

qubit[1] q

H q[0]
"""
        self.assertEqual(expected, output)


if __name__ == "__main__":
    unittest.main()
