# This integration test also serves as example and code documentation.

import unittest
from src.Circuit import Circuit
from test.TestGates import TEST_GATES


class IntegrationTest(unittest.TestCase):
    def test_simple(self):
        myCircuit = Circuit(TEST_GATES, """
                version 3.0

                qubit[3] qreg

                ry qreg[0], 1.23
                RY qreg[1], 2.34           // Aliases for gates can be defined, here ry == RY
                cnot qreg[0], qreg[1]
                rx qreg[0], -2.3
                ry qreg[1], -3.14
            """)
        
        #    Decompose CNOT as
        #
        #    -----•-----        ------- Z -------
        #         |        ==           |
        #    -----⊕----        --- H --•-- H ---
        #

        myCircuit.replace("cnot", lambda control, target: [("h", (target,)), ("cz", (control, target)), ("h", (target,))])
        
        # Do 1q-gate fusion and decompose with McKay decomposition.

        myCircuit.decompose_mckay()

        # Write the transformed circuit as a cQasm3 string.

        output = str(myCircuit)

        self.assertEqual(output, """version 3.0

qubit[3] qreg

rz qreg[0], 3.141592653589793
x90 qreg[0]
rz qreg[0], 1.9115926535897927
x90 qreg[0]
rz qreg[1], 3.141592653589793
x90 qreg[1]
rz qreg[1], 2.37238898038469
x90 qreg[1]
rz qreg[1], 3.141592653589793
cz qreg[0], qreg[1]
rz qreg[1], 3.141592653589793
x90 qreg[1]
rz qreg[1], 1.57238898038469
x90 qreg[1]
rz qreg[1], 3.141592653589793
rz qreg[0], 1.5707963267948966
x90 qreg[0]
rz qreg[0], 0.8415926535897933
x90 qreg[0]
rz qreg[0], 1.5707963267948966
""")

    def test_qi(self):
        myCircuit = Circuit(TEST_GATES, """
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
            RZ q[0], 1.5707963267949
            RY q[0], -0.2
            cnot q[1], q[0]
            RZ q[0], 1.5789
            cnot q[1], q[0]
            cnot q[1], q[2]
            RZ q[1], 2.5707963267949
            cr q[2], q[3], 2.123
            RY q[1], -1.5707963267949

            """)

        myCircuit.decompose_mckay()
        output = str(myCircuit)

        expected = """version 3.0

qubit[4] q

x90 q[1]
rz q[1], 1.5707963267948966
x90 q[1]
rz q[0], -0.20000000000000018
x90 q[0]
rz q[0], 1.5707963267948957
x90 q[0]
rz q[0], 1.5707963267949
cnot q[1], q[0]
rz q[0], -2.352142653589793
x90 q[0]
rz q[0], 3.141592653589793
x90 q[0]
rz q[0], 0.7894500000000004
cnot q[1], q[0]
x90 q[2]
rz q[2], 1.5707963267948966
x90 q[2]
cnot q[1], q[2]
cr q[2], q[3], 2.123
rz q[1], 2.5707963267949
x90 q[1]
rz q[1], 1.570796326794893
x90 q[1]
rz q[1], 3.141592653589793
"""
        
        self.assertEqual(output, expected)