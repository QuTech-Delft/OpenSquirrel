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

                ry qreg[0], 1.23
                RY qreg[1], 2.34           // Aliases for gates can be defined, here ry == RY
                cnot qreg[0], qreg[1]
                rx qreg[0], -2.3
                ry qreg[1], -3.14
            """
        )

        #    Decompose CNOT as
        #
        #    -----•-----        ------- Z -------
        #         |        ==           |
        #    -----⊕----        --- H --•-- H ---
        #

        myCircuit.replace(
            cnot,
            lambda control, target: [
                h(target),
                cz(control, target),
                h(target),
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

rz qreg[0], 3.1415927
x90 qreg[0]
rz qreg[0], 1.9115927
x90 qreg[0]
rz qreg[1], 3.1415927
x90 qreg[1]
rz qreg[1], 2.372389
x90 qreg[1]
rz qreg[1], 3.1415927
cz qreg[0], qreg[1]
rz qreg[0], 1.5707963
x90 qreg[0]
rz qreg[0], 0.84159265
x90 qreg[0]
rz qreg[0], 1.5707963
rz qreg[1], 3.1415927
x90 qreg[1]
rz qreg[1], 1.572389
x90 qreg[1]
rz qreg[1], 3.1415927
""",
        )

    def test_qi(self):
        myCircuit = Circuit.from_string(
            """
            version 3.0

            // This is a single line comment which ends on the newline.
            // The cQASM string must begin with the version instruction even before any comments.

            /* This is a multi-
            line comment block */


            qubit[4] q   //declaration

            //let us create a Bell state on 2 qubits and a |+> state on the third qubit

            H q[2]
            H q[1]
            H q[0]
            RZ q[0], 1.5707963
            RY q[0], -0.2
            cnot q[1], q[0]
            RZ q[0], 1.5789
            cnot q[1], q[0]
            cnot q[1], q[2]
            RZ q[1], 2.5707963
            cr q[2], q[3], 2.123
            RY q[1], -1.5707963

            """
        )

        myCircuit.merge_single_qubit_gates()

        myCircuit.decompose(decomposer=McKayDecomposer)
        output = str(myCircuit)

        expected = """version 3.0

qubit[4] q

x90 q[1]
rz q[1], 1.5707963
x90 q[1]
rz q[0], -0.2
x90 q[0]
rz q[0], 1.5707963
x90 q[0]
rz q[0], 1.5707963
cnot q[1], q[0]
rz q[0], -2.3521427
x90 q[0]
rz q[0], 3.1415927
x90 q[0]
rz q[0], 0.78945
cnot q[1], q[0]
x90 q[2]
rz q[2], 1.5707963
x90 q[2]
cnot q[1], q[2]
cr q[2], q[3], 2.123
rz q[1], 2.5707963
x90 q[1]
rz q[1], 1.5707964
x90 q[1]
rz q[1], 3.1415927
"""

        self.assertEqual(output, expected)

    def test_libqasm_error(self):
        with self.assertRaisesRegex(
            Exception,
            r"Parsing error: Error at <unknown>:4:21\.\.23: failed to resolve overload for ry with argument pack \(qubit, real, int\)",
        ):
            Circuit.from_string(
                """
                    version 3.0
                    qubit[3] qreg
                    ry qreg[0], 1.23, 1
                """,
                use_libqasm=True,
            )

    @unittest.skipIf(
        importlib.util.find_spec("quantify_scheduler") is None, reason="quantify_scheduler is not installed"
    )
    def test_export_quantify_scheduler(self):
        myCircuit = Circuit.from_string(
            """
                version 3.0

                qubit[3] qreg

                h qreg[1]
                crk qreg[0], qreg[1], 4
                h qreg[0]
            """
        )

        myCircuit.decompose(decomposer=CNOTDecomposer)
        myCircuit.replace(
            cnot,
            lambda control, target: [
                h(target),
                cz(control, target),
                h(target),
            ],
        )
        myCircuit.merge_single_qubit_gates()
        myCircuit.decompose(decomposer=ZYZDecomposer)  # FIXME: for best gate count we need a Z-XY decomposer.

        exported_schedule = myCircuit.export(format=ExportFormat.QUANTIFY_SCHEDULER)

        self.assertEqual(exported_schedule.name, "Exported OpenSquirrel circuit")

        operation_ids = [v["operation_id"] for k, v in exported_schedule.schedulables.items()]
        operations = [exported_schedule.operations[operation_id].name for operation_id in operation_ids]

        self.assertEqual(
            operations,
            [
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
