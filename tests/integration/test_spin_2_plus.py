from typing import cast

import pytest

from opensquirrel import Circuit
from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
from opensquirrel.common import are_matrices_equivalent_up_to_global_phase
from opensquirrel.passes.decomposer import McKayDecomposer
from opensquirrel.passes.decomposer.can2cz_decomposer import Can2CZDecomposer
from opensquirrel.passes.merger import SingleQubitGatesMerger
from opensquirrel.passes.validator import InteractionValidator, PrimitiveGateValidator
from tests import STATIC_DATA
from tests.integration import DataType

BACKEND_ID = "spin-2-plus"


class TestSpin2Plus:
    @pytest.fixture
    def data(self) -> DataType:
        """
        Spin-2+ chip topology:
            0 <--> 1
        """
        return cast("DataType", STATIC_DATA["backends"][BACKEND_ID])

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
            qubit[2] q  // Sping-2+ has a 2-qubit register
            bit[4] b

            // Initialization
            init q

            // Single-qubit gates
            I q[0]
            H q[1]
            X q[0]
            X90 q[1]
            mX90 q[0]
            Y q[1]
            Y90 q[0]
            mY90 q[1]
            Z q[0]
            S q[1]
            Sdag q[0]
            T q[1]
            Tdag q[0]
            Rx(pi/2) q[1]
            Ry(pi/2) q[0]
            Rz(tau) q[1]

            // Mid-circuit measurement
            b[0,2] = measure q

            // Two-qubit gates
            CNOT q[0], q[1]
            CZ q[1], q[0]
            SWAP q[0], q[1]

            // Control instructions
            barrier q
            wait(3) q

            // Final measurement
            b[1,3] = measure q
            """,
        )
        circuit.validate(validator=InteractionValidator(**data))

        # Platform-dependent decomposition order can differ while preserving the same unitary.
        expected_matrix = get_circuit_matrix(circuit)
        expected_measurement_to_bit_map = dict(circuit.measurement_to_bit_map)

        circuit.decompose(decomposer=Can2CZDecomposer(**data))
        circuit.merge(merger=SingleQubitGatesMerger(**data))
        circuit.decompose(decomposer=McKayDecomposer(**data))
        circuit.validate(validator=PrimitiveGateValidator(**data))

        actual_matrix = get_circuit_matrix(circuit)
        assert are_matrices_equivalent_up_to_global_phase(actual_matrix, expected_matrix)
        assert dict(circuit.measurement_to_bit_map) == expected_measurement_to_bit_map
