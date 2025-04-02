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
from opensquirrel.passes.validator import PrimitiveGateValidator, RoutingValidator


def test_spin2plus_backend() -> None:
    qc = Circuit.from_string(
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
        CR(pi) q[0], q[1]
        CRk(2) q[1], q[0]
        SWAP q[0], q[1]

        // Control instructions
        barrier q
        wait(3) q

        // Final measurement
        b[1,3] = measure q
        """,
    )

    """
    Spin-2+ chip topology:
        0 <--> 1
    """
    connectivity = {"0": [1], "1": [0]}

    primitive_gate_set = ["I", "X90", "mX90", "Y90", "mY90", "Rz", "CZ", "measure", "wait", "init", "barrier"]

    # Validate that the interactions in the circuit are possible given the chip topology
    qc.validate(validator=RoutingValidator(connectivity))

    # Decompose SWAP gate into 3 CNOT gates
    qc.decompose(decomposer=SWAP2CNOTDecomposer())

    # Decompose 2-qubit gates to a decomposition where the 2-qubit interactions are captured by CNOT gates
    qc.decompose(decomposer=CNOTDecomposer())

    # Replace CNOT gates with CZ gates
    qc.decompose(decomposer=CNOT2CZDecomposer())

    # Merge single-qubit gates
    qc.merge(merger=SingleQubitGatesMerger())

    # Decompose single-qubit gates to primitive gates with McKay decomposer
    qc.decompose(decomposer=McKayDecomposer())

    # Validate that the compiled circuit is composed of gates that are in the primitive gate set
    qc.validate(validator=PrimitiveGateValidator(primitive_gate_set))

    assert (
        str(qc)
        == """version 3.0

qubit[2] q
bit[4] b

init q[0]
init q[1]
Rz(1.5707963) q[0]
X90 q[0]
Rz(0.78539813) q[0]
X90 q[0]
Rz(-1.5707964) q[0]
b[0] = measure q[0]
Rz(2.3561946) q[1]
X90 q[1]
Rz(-3.1415927) q[1]
b[2] = measure q[1]
Rz(1.5707963) q[1]
X90 q[1]
Rz(-1.5707963) q[1]
CZ q[0], q[1]
Rz(-1.5707963) q[1]
X90 q[1]
Rz(1.5707963) q[1]
Rz(3.1415927) q[0]
CZ q[1], q[0]
Rz(3.1415927) q[0]
Rz(3.1415927) q[1]
CZ q[0], q[1]
Rz(3.1415927) q[1]
Rz(2.3561944) q[0]
X90 q[0]
Rz(-1.5707963) q[0]
CZ q[1], q[0]
Rz(-1.5707963) q[0]
X90 q[0]
Rz(2.3561946) q[0]
X90 q[0]
Rz(-1.5707963) q[0]
CZ q[1], q[0]
Rz(-1.5707963) q[0]
X90 q[0]
Rz(1.5707963) q[0]
Rz(2.3561944) q[1]
X90 q[1]
Rz(-1.5707963) q[1]
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
Rz(-1.5707963) q[1]
X90 q[1]
Rz(1.5707963) q[1]
barrier q[0]
barrier q[1]
wait(3) q[0]
wait(3) q[1]
b[1] = measure q[0]
b[3] = measure q[1]
"""
    )


def test_hectoqubit_backend() -> None:
    qc = Circuit.from_string(
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

    # HectoQubit/2 chip is Tuna-5 (full-connectivity assumed for now)
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

    # Validate that the interactions in the circuit are possible given the chip topology
    qc.validate(validator=RoutingValidator(connectivity))

    # Decompose SWAP gate into 3 CNOT gates
    qc.decompose(decomposer=SWAP2CNOTDecomposer())

    # Decompose 2-qubit gates to a decomposition where the 2-qubit interactions are captured by CNOT gates
    qc.decompose(decomposer=CNOTDecomposer())

    # Replace CNOT gates with CZ gates
    qc.decompose(decomposer=CNOT2CZDecomposer())

    # Merge single-qubit gates
    qc.merge(merger=SingleQubitGatesMerger())

    # Decompose single-qubit gates to primitive gates with the XYX decomposer
    qc.decompose(decomposer=XYXDecomposer())

    # Validate that the compiled circuit is composed of gates that are in the primitive gate set
    qc.validate(validator=PrimitiveGateValidator(primitive_gate_set))

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
            "Rxy(-90, 0, 'q[3]')",
            "Rxy(180, 90, 'q[3]')",
            "Rxy(90, 0, 'q[3]')",
            "CZ (q[2], q[3])",
            "Rxy(-90, 0, 'q[0]')",
            "Rxy(180, 90, 'q[0]')",
            "Rxy(90, 0, 'q[0]')",
            "CZ (q[4], q[0])",
            "Rxy(90, 90, 'q[1]')",
            "Rxy(180, 0, 'q[2]')",
            "Rxy(90, 90, 'q[2]')",
            "Rxy(135, 0, 'q[2]')",
            "CZ (q[1], q[2])",
            "Rxy(45, 0, 'q[2]')",
            "CZ (q[1], q[2])",
            "Rxy(-90, 0, 'q[3]')",
            "Rxy(180, 90, 'q[3]')",
            "Rxy(90, 0, 'q[3]')",
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
            "Rxy(-90, 0, 'q[0]')",
            "Rxy(180, 90, 'q[0]')",
            "Rxy(90, 0, 'q[0]')",
            "Rxy(-90, 0, 'q[1]')",
            "Rxy(45, 90, 'q[1]')",
            "Rxy(90, 0, 'q[1]')",
            "Rxy(90, 90, 'q[2]')",
            "Rxy(90, 90, 'q[4]')",
            "Measure q[0]",
            "Measure q[1]",
            "Measure q[2]",
            "Measure q[3]",
            "Measure q[4]",
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


def test_starmon7_backend() -> None:
    qc = Circuit.from_string(
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

    """
    Starmon-7 chip topology:
       1 = 4 = 6
       \\     //
           3
       //     \\
       0 = 2 = 5
    """

    connectivity = {
        "0": [2, 3],
        "1": [3, 4],
        "2": [0, 5],
        "3": [0, 1, 5, 6],
        "4": [1, 6],
        "5": [2, 3],
        "6": [3, 4],
    }

    primitive_gate_set = [
        "I",
        "H",
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
        "CR",
        "CRk",
        "SWAP",
        "measure",
        "wait",
        "init",
        "barrier",
    ]

    # Validate that the interactions in the circuit are possible given the chip topology
    qc.validate(validator=RoutingValidator(connectivity))

    # Validate that the compiled circuit is composed of gates that are in the primitive gate set
    qc.validate(validator=PrimitiveGateValidator(primitive_gate_set))

    exported_circuit = qc.export(fmt=ExportFormat.CQASM_V1)

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
rz q[1], 6.2831853
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
