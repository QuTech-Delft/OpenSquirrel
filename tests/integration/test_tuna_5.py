import importlib
from typing import Any, Union

import pytest

from opensquirrel import Circuit, Measure
from opensquirrel.passes.decomposer import CZDecomposer, SWAP2CZDecomposer, XYXDecomposer
from opensquirrel.passes.exporter import ExportFormat
from opensquirrel.passes.merger import SingleQubitGatesMerger
from opensquirrel.passes.validator import InteractionValidator, PrimitiveGateValidator

DataType = dict[str, Any]
BitStringMappingType = list[Union[tuple[None, None], tuple[int, int]]]


def _get_operations(exported_schedule) -> list[str]:  # type: ignore  # noqa: ANN001
    return [
        exported_schedule.operations[schedulable["operation_id"]].name
        for schedulable in exported_schedule.schedulables.values()
    ]


def _check_bitstring_mapping(circuit: Circuit, exported_schedule, bitstring_mapping: BitStringMappingType) -> None:  # type: ignore  # noqa: ANN001
    ir_measures = [instruction for instruction in circuit.ir.statements if isinstance(instruction, Measure)]
    ir_acq_index_record = [0] * circuit.qubit_register_size
    ir_bitstring_mapping = [(None, None)] * circuit.bit_register_size

    qs_measures = [
        operation.data["gate_info"]
        for operation in exported_schedule.operations.values()
        if operation.data["gate_info"]["operation_type"] == "measure"
    ]

    for i, ir_measure in enumerate(ir_measures):
        qubit_index = ir_measure.qubit.index
        ir_acq_index = ir_acq_index_record[qubit_index]
        ir_bitstring_mapping[ir_measure.bit.index] = (ir_acq_index, qubit_index)  # type: ignore
        assert qs_measures[i]["acq_channel_override"] == qubit_index
        assert qs_measures[i]["acq_index"] == ir_acq_index
        assert qs_measures[i]["acq_protocol"] == "ThresholdedAcquisition"
        ir_acq_index_record[qubit_index] += 1

    assert len(bitstring_mapping) == circuit.bit_register_size
    assert bitstring_mapping == ir_bitstring_mapping


class TestTuna5:
    @pytest.fixture
    def qs_is_installed(self) -> bool:
        return importlib.util.find_spec("quantify_scheduler") is not None

    @pytest.fixture
    def data(self) -> DataType:
        # Tuna-5 (full-connectivity assumed for now)
        connectivity = {
            "0": [1, 2, 3, 4],
            "1": [0, 2, 3, 4],
            "2": [0, 1, 3, 4],
            "3": [0, 1, 2, 4],
            "4": [0, 1, 2, 3],
        }
        primitive_gate_set = [
            "I",
            "X",
            "X90",
            "mX90",
            "Y",
            "Y90",
            "mY90",
            "Z",
            "S",
            "Sdag",
            "T",
            "Tdag",
            "Rx",
            "Ry",
            "Rz",
            "CNOT",
            "CZ",
            "measure",
            "wait",
            "init",
            "barrier",
        ]
        return {
            "connectivity": connectivity,
            "primitive_gate_set": primitive_gate_set,
        }

    def test_qs_is_not_installed(self, qs_is_installed: bool) -> None:
        circuit = Circuit.from_string("""version 3.0;""")
        if not qs_is_installed:
            with pytest.raises(
                Exception,
                match="quantify-scheduler is not installed, or cannot be installed on your system",
            ):
                circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)

    def test_complete_circuit(self, qs_is_installed: bool, data: DataType) -> None:
        circuit = Circuit.from_string(
            """
            // Version statement
            version 3.0

            // This is a single line comment which ends on the newline.
            // The cQASM string must begin with the version instruction (apart from any preceding comments).

            /* This is a multi-
            line comment block */

            // (Qu)bit declaration
            qubit[5] q  // Tuna-5 has a 5-qubit register
            bit[7] b

            // Initialization
            init q

            // Single-qubit gates
            I q[0]
            H q[1]
            X q[2]
            X90 q[3]
            mX90 q[4]
            Y q[0]
            Y90 q[1]
            mY90 q[2]
            Z q[3]
            S q[4]
            Sdag q[0]
            T q[1]
            Tdag q[2]
            Rx(pi/2) q[3]
            Ry(pi/2) q[4]
            Rz(tau) q[0]

            barrier q  // to ensure all measurements occur simultaneously
            // Mid-circuit measurement
            b[0:4] = measure q

            // Two-qubit gates
            CNOT q[0], q[1]
            CZ q[2], q[3]
            CR(pi) q[4], q[0]
            CRk(2) q[1], q[2]
            SWAP q[3], q[4]

            // Control instructions
            barrier q
            // wait(3) q  // not supported by HectoQubit/2 atm

            // Final measurement
            b[2:6] = measure q
            """
        )
        circuit.validate(validator=InteractionValidator(**data))
        circuit.decompose(decomposer=SWAP2CZDecomposer(**data))
        circuit.decompose(decomposer=CZDecomposer(**data))
        circuit.merge(merger=SingleQubitGatesMerger(**data))
        circuit.decompose(decomposer=XYXDecomposer(**data))
        circuit.validate(validator=PrimitiveGateValidator(**data))

        if qs_is_installed:
            exported_schedule, bitstring_mapping = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
            operations = _get_operations(exported_schedule)

            assert exported_schedule.name == "Exported OpenSquirrel circuit"
            assert operations == [
                "Rxy(90, 0, 'q[0]')",
                "Rxy(90, 90, 'q[0]')",
                "Rxy(90, 0, 'q[0]')",
                "Rxy(90, 0, 'q[1]')",
                "Rxy(45, 90, 'q[1]')",
                "Rxy(90, 0, 'q[1]')",
                "Rxy(-45, 0, 'q[2]')",
                "Rxy(90, 90, 'q[2]')",
                "Rxy(180, 0, 'q[2]')",
                "Rxy(-90, 0, 'q[3]')",
                "Rxy(180, 90, 'q[3]')",
                "Rxy(90, 0, 'q[3]')",
                "Rxy(-90, 0, 'q[4]')",
                "Rxy(90, 90, 'q[4]')",
                "Rxy(90, 0, 'q[4]')",
                "Measure q[0]",
                "Measure q[1]",
                "Measure q[2]",
                "Measure q[3]",
                "Measure q[4]",
                "Rxy(180, 0, 'q[1]')",
                "Rxy(90, 90, 'q[1]')",
                "Rxy(180, 0, 'q[1]')",
                "CZ (q[0], q[1])",
                "CZ (q[2], q[3])",
                "CZ (q[4], q[0])",
                "Rxy(90, 90, 'q[1]')",
                "Rxy(-90, 0, 'q[2]')",
                "CZ (q[1], q[2])",
                "Rxy(180, 0, 'q[2]')",
                "Rxy(45, 90, 'q[2]')",
                "Rxy(180, 0, 'q[2]')",
                "CZ (q[1], q[2])",
                "Rxy(180, 0, 'q[4]')",
                "Rxy(90, 90, 'q[4]')",
                "Rxy(180, 0, 'q[4]')",
                "CZ (q[3], q[4])",
                "Rxy(90, 90, 'q[4]')",
                "Rxy(180, 0, 'q[3]')",
                "Rxy(90, 90, 'q[3]')",
                "Rxy(180, 0, 'q[3]')",
                "CZ (q[4], q[3])",
                "Rxy(90, 90, 'q[3]')",
                "Rxy(180, 0, 'q[4]')",
                "Rxy(90, 90, 'q[4]')",
                "Rxy(180, 0, 'q[4]')",
                "CZ (q[3], q[4])",
                "Rxy(-90, 0, 'q[1]')",
                "Rxy(45, 90, 'q[1]')",
                "Rxy(90, 0, 'q[1]')",
                "Rxy(45, 90, 'q[2]')",
                "Rxy(90, 0, 'q[2]')",
                "Rxy(90, 90, 'q[4]')",
                "Measure q[0]",
                "Measure q[1]",
                "Measure q[2]",
                "Measure q[3]",
                "Measure q[4]",
            ]
            _check_bitstring_mapping(circuit, exported_schedule, bitstring_mapping)

    def test_all_xy(self, qs_is_installed: bool, data: DataType) -> None:
        circuit = Circuit.from_string(
            """
            version 3.0

            qubit[3] q
            bit[10] b

            reset q

            Rx(0.0) q[0]
            Rx(0.0) q[0]
            b[0] = measure q[0]

            Rx(3.141592653589793) q[1]
            Rx(3.141592653589793) q[1]
            b[1] = measure q[1]

            Ry(3.141592653589793) q[0]
            Ry(3.141592653589793) q[0]
            b[2] = measure q[0]

            Rx(3.141592653589793) q[2]
            Ry(3.141592653589793) q[2]
            b[3] = measure q[2]

            Ry(3.141592653589793) q[0]
            Rx(3.141592653589793) q[0]
            b[4] = measure q[0]

            Rx(3.141592653589793) q[0]
            Rx(0.0) q[0]
            Ry(3.141592653589793) q[2]
            Rx(0.0) q[2]
            Rx(1.5707963267948966) q[1]
            Rx(1.5707963267948966) q[1]

            b[6] = measure q[2]
            b[5] = measure q[0]
            b[8] = measure q[0]
            b[7] = measure q[1]

            b[9] = measure q[0]
            """
        )
        # No compilation passes are performed
        if qs_is_installed:
            exported_schedule, bitstring_mapping = circuit.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
            operations = _get_operations(exported_schedule)

            assert exported_schedule.name == "Exported OpenSquirrel circuit"
            assert operations == [
                "Reset q[0]",
                "Reset q[1]",
                "Reset q[2]",
                "Rxy(0, 0, 'q[0]')",
                "Rxy(0, 0, 'q[0]')",
                "Measure q[0]",
                "Rxy(180, 0, 'q[1]')",
                "Rxy(180, 0, 'q[1]')",
                "Measure q[1]",
                "Rxy(180, 90, 'q[0]')",
                "Rxy(180, 90, 'q[0]')",
                "Measure q[0]",
                "Rxy(180, 0, 'q[2]')",
                "Rxy(180, 90, 'q[2]')",
                "Measure q[2]",
                "Rxy(180, 90, 'q[0]')",
                "Rxy(180, 0, 'q[0]')",
                "Measure q[0]",
                "Rxy(180, 0, 'q[0]')",
                "Rxy(0, 0, 'q[0]')",
                "Rxy(180, 90, 'q[2]')",
                "Rxy(0, 0, 'q[2]')",
                "Rxy(90, 0, 'q[1]')",
                "Rxy(90, 0, 'q[1]')",
                "Measure q[2]",
                "Measure q[0]",
                "Measure q[0]",
                "Measure q[1]",
                "Measure q[0]",
            ]
            _check_bitstring_mapping(circuit, exported_schedule, bitstring_mapping)
