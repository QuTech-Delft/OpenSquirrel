# This integration test also serves as example and code documentation.
from __future__ import annotations

import importlib.util

import pytest

from opensquirrel.circuit import Circuit
from opensquirrel.ir import Measure
from opensquirrel.passes.decomposer import (
    CNOT2CZDecomposer,
    CNOTDecomposer,
    McKayDecomposer,
    SWAP2CNOTDecomposer,
    XYXDecomposer,
)
from opensquirrel.passes.exporter import ExportFormat
from opensquirrel.passes.merger import SingleQubitGatesMerger
from opensquirrel.passes.validator import NativeGateValidator, RoutingValidator


def test_spin2plus_backend() -> None:
    qc = Circuit.from_string(
        """
        version 3.0

        // This is a single line comment which ends on the newline.
        // The cQASM string must begin with the version instruction (apart from any preceding comments).

        /* This is a multi-
        line comment block */

        qubit[2] q
        bit[4] b

        H q[0:1]
        Rx(1.5789) q[0]
        Ry(-0.2) q[0]
        Rz(1.5707963) q[0]
        CNOT q[1], q[0]
        CR(2.123) q[0], q[1]
        CRk(2) q[0], q[1]
        SWAP q[0], q[1]
        b[1,3] = measure q
        """,
    )

    # Check whether the above algorithm can be mapped to a dummy chip topology
    connectivity = {"0": [1], "1": [0]}
    native_gate_set = ["I", "X90", "mX90", "Y90", "mY90", "Rz", "CZ"]

    qc.validate(validator=RoutingValidator(connectivity))

    # Decompose 2-qubit gates to a decomposition where the 2-qubit interactions are captured by CNOT gates
    qc.decompose(decomposer=CNOTDecomposer())

    qc.decompose(decomposer=SWAP2CNOTDecomposer())

    # Decompose 2-qubit gates to a decomposition where the 2-qubit interactions are captured by CNOT gates
    qc.decompose(decomposer=CNOTDecomposer())

    # Replace CNOT gates with CZ gates
    qc.decompose(decomposer=CNOT2CZDecomposer())

    # Merge single-qubit gates
    qc.merge(merger=SingleQubitGatesMerger())

    # Decompose single-qubit gates to spin backend native gates with McKay decomposer
    qc.decompose(decomposer=McKayDecomposer())

    # Check whether the gates in the circuit match the native gate set of the backend
    qc.validate(validator=NativeGateValidator(native_gate_set))

    assert (
        str(qc)
        == """version 3.0

qubit[2] q
bit[4] b

Rz(1.5707963) q[1]
X90 q[1]
Rz(1.5707963) q[1]
Rz(1.5789) q[0]
X90 q[0]
Rz(-2.9415926) q[0]
CZ q[1], q[0]
Rz(-1.5707963) q[0]
X90 q[0]
Rz(1.5707963) q[0]
Rz(2.6322964) q[1]
X90 q[1]
Rz(-1.5707963) q[1]
CZ q[0], q[1]
Rz(-1.5707963) q[1]
X90 q[1]
Rz(2.0800926) q[1]
X90 q[1]
Rz(-1.5707963) q[1]
CZ q[0], q[1]
Rz(1.0615) q[0]
Rz(1.5707963) q[1]
X90 q[1]
Rz(2.3561946) q[1]
X90 q[1]
Rz(1.5707963) q[1]
CZ q[0], q[1]
Rz(-1.5707963) q[1]
X90 q[1]
Rz(2.3561946) q[1]
X90 q[1]
Rz(-1.5707963) q[1]
CZ q[0], q[1]
Rz(0.78539816) q[0]
CZ q[0], q[1]
Rz(-1.5707963) q[1]
X90 q[1]
Rz(1.5707963) q[1]
Rz(1.5707963) q[0]
X90 q[0]
Rz(-1.5707963) q[0]
CZ q[1], q[0]
Rz(-1.5707963) q[0]
X90 q[0]
Rz(1.5707963) q[0]
Rz(1.5707963) q[1]
X90 q[1]
Rz(-1.5707963) q[1]
CZ q[0], q[1]
b[1] = measure q[0]
Rz(-1.5707963) q[1]
X90 q[1]
Rz(1.5707963) q[1]
b[3] = measure q[1]
"""
    )


def test_hectoqubit_backend() -> None:
    qc = Circuit.from_string(
        """
        version 3.0

        qubit[3] q
        bit[3] b

        H q[1]
        CZ q[0], q[1]
        CNOT q[0], q[1]
        CRk(4) q[0], q[1]
        H q[0]
        b[1:2] = measure q[0:1]
        """
    )

    # Decompose 2-qubit gates to a decomposition where the 2-qubit interactions are captured by CNOT gates
    qc.decompose(decomposer=CNOTDecomposer())

    # Replace CNOT gates with CZ gates
    qc.decompose(decomposer=CNOT2CZDecomposer())

    # Merge single-qubit gates
    qc.merge(merger=SingleQubitGatesMerger())

    # Decompose single-qubit gates to HectoQubit backend native gates with the XYX decomposer
    qc.decompose(decomposer=XYXDecomposer())

    if importlib.util.find_spec("quantify_scheduler") is None:
        with pytest.raises(
            Exception,
            match="quantify-scheduler is not installed, or cannot be installed on your system",
        ):
            qc.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
    else:
        exported_schedule, bit_string_mapping = qc.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)

        assert exported_schedule.name == "Exported OpenSquirrel circuit"

        operations = [
            exported_schedule.operations[schedulable["operation_id"]].name
            for schedulable in exported_schedule.schedulables.values()
        ]

        assert operations == [
            "Rxy(180, 0, 'q[1]')",
            "Rxy(90, 90, 'q[1]')",
            "Rxy(180, 0, 'q[1]')",
            "CZ (q[0], q[1])",
            "Rxy(180, 0, 'q[1]')",
            "Rxy(90, 90, 'q[1]')",
            "CZ (q[0], q[1])",
            "Rxy(-11.25, 0, 'q[1]')",
            "CZ (q[0], q[1])",
            "Rxy(11.25, 0, 'q[1]')",
            "CZ (q[0], q[1])",
            "Rxy(180, 0, 'q[0]')",
            "Rxy(-90, 90, 'q[0]')",
            "Rxy(11.25, 0, 'q[0]')",
            "Measure q[0]",
            "Rxy(90, 90, 'q[1]')",
            "Measure q[1]",
        ]

        ir_measures = [instruction for instruction in qc.ir.statements if isinstance(instruction, Measure)]
        qs_measures = [
            operation.data["gate_info"]
            for operation in exported_schedule.operations.values()
            if operation.data["gate_info"]["operation_type"] == "measure"
        ]

        ir_acq_index_record = [0] * qc.qubit_register_size
        ir_bit_string_mapping: list[tuple[None, None] | tuple[int, int]] = [(None, None)] * qc.bit_register_size
        for i, ir_measure in enumerate(ir_measures):
            qubit_index = ir_measure.qubit.index
            ir_acq_index = ir_acq_index_record[qubit_index]
            ir_bit_string_mapping[ir_measure.bit.index] = (ir_acq_index, qubit_index)
            assert qs_measures[i]["acq_channel_override"] == qubit_index
            assert qs_measures[i]["acq_index"] == ir_acq_index
            assert qs_measures[i]["acq_protocol"] == "ThresholdedAcquisition"
            ir_acq_index_record[qubit_index] += 1

        assert len(bit_string_mapping) == qc.bit_register_size
        assert bit_string_mapping == ir_bit_string_mapping


def test_hectoqubit_backend_allxy() -> None:
    qc = Circuit.from_string(
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

    if importlib.util.find_spec("quantify_scheduler") is None:
        with pytest.raises(
            Exception,
            match="quantify-scheduler is not installed, or cannot be installed on your system",
        ):
            qc.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)
    else:
        exported_schedule, bit_string_mapping = qc.export(fmt=ExportFormat.QUANTIFY_SCHEDULER)

        assert exported_schedule.name == "Exported OpenSquirrel circuit"

        operations = [
            exported_schedule.operations[schedulable["operation_id"]].name
            for schedulable in exported_schedule.schedulables.values()
        ]

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

        qs_measures = [
            operation.data["gate_info"]
            for operation in exported_schedule.operations.values()
            if operation.data["gate_info"]["operation_type"] == "measure"
        ]

        ir_measures = [instruction for instruction in qc.ir.statements if isinstance(instruction, Measure)]

        ir_acq_index_record = [0] * qc.qubit_register_size
        ir_bit_string_mapping: list[tuple[None, None] | tuple[int, int]] = [(None, None)] * qc.bit_register_size
        for i, ir_measurement in enumerate(ir_measures):
            qubit_index = ir_measurement.qubit.index
            ir_acq_index = ir_acq_index_record[qubit_index]
            ir_bit_string_mapping[ir_measurement.bit.index] = (
                ir_acq_index,
                qubit_index,
            )
            assert qs_measures[i]["acq_channel_override"] == qubit_index
            assert qs_measures[i]["acq_index"] == ir_acq_index
            assert qs_measures[i]["acq_protocol"] == "ThresholdedAcquisition"
            ir_acq_index_record[qubit_index] += 1

        assert len(bit_string_mapping) == qc.bit_register_size
        assert bit_string_mapping == ir_bit_string_mapping
