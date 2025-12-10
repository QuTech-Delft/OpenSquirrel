from typing import cast

import pytest

from opensquirrel import Circuit
from opensquirrel.passes.exporter import CqasmV1Exporter
from opensquirrel.passes.validator import InteractionValidator, PrimitiveGateValidator
from tests import STATIC_DATA
from tests.integration import DataType

BACKEND_ID = "starmon-7"


class TestStarmon7:
    @pytest.fixture
    def data(self) -> DataType:
        """
        Starmon-7 chip topology:
           1 = 4 = 6
           \\     //
               3
           //     \\
           0 = 2 = 5
        """
        return cast(DataType, STATIC_DATA["backends"][BACKEND_ID])

    def test_complete_circuit(self, data: DataType) -> None:
        circuit = Circuit.from_string(
            """
            // Version statement
            version 3.0

            // This is a single line comment which ends on the newline.
            // The cQASM string must begin with the version instruction (apart from any preceding comments).

            /* This is a multi-
            line comment block */

            // (Qu)bit declaration
            qubit[7] q  // Starmon-7 has a 7-qubit register
            bit[14] b

            // Initialization
            init q

            // Single-qubit gates
            I q[0]
            H q[1]
            X q[2]
            X90 q[3]
            mX90 q[4]
            Y q[5]
            Y90 q[6]
            mY90 q[0]
            Z q[1]
            S q[2]
            Sdag q[3]
            T q[4]
            Tdag q[5]
            Rx(pi/2) q[6]
            Ry(pi/2) q[0]
            Rz(tau) q[1]

            barrier q  // to ensure all measurements occur simultaneously
            // Mid-circuit measurement
            b[0:6] = measure q

            // Two-qubit gates
            CNOT q[0], q[2]
            CZ q[1], q[4]
            CR(pi) q[5], q[3]
            CRk(2) q[3], q[6]
            SWAP q[5], q[2]

            // Control instructions
            barrier q
            wait(3) q

            // Final measurement
            b[7:13] = measure q
            """,
        )
        circuit.validate(validator=InteractionValidator(**data))
        circuit.validate(validator=PrimitiveGateValidator(**data))
        exported_circuit = circuit.export(exporter=CqasmV1Exporter())

        assert (
            exported_circuit
            == """version 1.0

qubits 7

prep_z q[0]
prep_z q[1]
prep_z q[2]
prep_z q[3]
prep_z q[4]
prep_z q[5]
prep_z q[6]
i q[0]
h q[1]
x q[2]
x90 q[3]
mx90 q[4]
y q[5]
y90 q[6]
my90 q[0]
z q[1]
s q[2]
sdag q[3]
t q[4]
tdag q[5]
rx q[6], 1.5707963
ry q[0], 1.5707963
rz q[1], 0.0
barrier q[0, 1, 2, 3, 4, 5, 6]
measure_z q[0]
measure_z q[1]
measure_z q[2]
measure_z q[3]
measure_z q[4]
measure_z q[5]
measure_z q[6]
cnot q[0], q[2]
cz q[1], q[4]
cr(3.1415927) q[5], q[3]
crk(2) q[3], q[6]
swap q[5], q[2]
barrier q[0, 1, 2, 3, 4, 5, 6]
wait q[0], 3
wait q[1], 3
wait q[2], 3
wait q[3], 3
wait q[4], 3
wait q[5], 3
wait q[6], 3
measure_z q[0]
measure_z q[1]
measure_z q[2]
measure_z q[3]
measure_z q[4]
measure_z q[5]
measure_z q[6]
"""
        )
