import numpy as np
import pytest

from opensquirrel import CircuitBuilder, Circuit
from opensquirrel.exceptions import UnsupportedGateError
from opensquirrel.exporter.export_format import ExportFormat
from opensquirrel.ir import Bit, BlochSphereRotation, ControlledGate, Float, Gate, MatrixGate, Qubit


def test_cqasm_v3_to_cqasm_v1() -> None:
    cqasm_v3_string = Circuit.from_string(
            """
    version 3.0

    qubit[2] q
    bit[2] b

    reset q
    I q[0]
    H q[0]
    CNOT q[0], q[1]
    Rx(5.123) q[0]
    b = measure q
    """
        )
    cqasm_v1_string = cqasm_v3_string.export(fmt=ExportFormat.CQASM_V1)
    assert cqasm_v1_string == """version 1.0

qubits 2

prep_z q[0]
prep_z q[1]
i q[0]
h q[0]
cnot q[0], q[1]
rx q[0], 5.123
measure_z q[0]
measure_z q[1]
"""


def test_version_statement() -> None:
    qc = Circuit.from_string("""version 3.0""")
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert cqasm_v1_string == """version 1.0
"""


def test_qubit_statement() -> None:
    builder = CircuitBuilder(3)
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert cqasm_v1_string == """version 1.0

qubits 3
"""


def test_circuit_to_string_after_circuit_modification() -> None:
    builder = CircuitBuilder(3)
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert cqasm_v1_string == """version 1.0

qubits 3
"""

    builder.H(Qubit(0))
    builder.CNOT(Qubit(0), Qubit(1))
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert cqasm_v1_string == """version 1.0

qubits 3

h q[0]
cnot q[0], q[1]
"""


def test_float_precision() -> None:
    builder = CircuitBuilder(3)
    builder.Rx(Qubit(0), Float(1.6546514861321684321654))
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert cqasm_v1_string == """version 1.0

qubits 3

rx q[0], 1.6546515
"""


def test_measure() -> None:
    builder = CircuitBuilder(1, 1)
    builder.H(Qubit(0))
    builder.measure(Qubit(0), Bit(0))
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert cqasm_v1_string == """version 1.0

qubits 1

h q[0]
measure_z q[0]
"""


def test_reset() -> None:
    builder = CircuitBuilder(1, 1)
    builder.H(Qubit(0))
    builder.reset(Qubit(0))
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert cqasm_v1_string == """version 1.0

qubits 1

h q[0]
prep_z q[0]
"""


def test_all_supported_gates() -> None:
    builder = CircuitBuilder(2,2)
    builder.reset(Qubit(0)).reset(Qubit(1))
    builder.I(Qubit(0)).X(Qubit(0)).Y(Qubit(0)).Z(Qubit(0))
    builder.Rx(Qubit(0), Float(1.234)).Ry(Qubit(0), Float(-1.234)).Rz(Qubit(0), Float(1.234))
    builder.X90(Qubit(0)).Y90(Qubit(0))
    builder.mX90(Qubit(0)).mY90(Qubit(0))
    builder.S(Qubit(0)).Sdag(Qubit(0)).T(Qubit(0)).Tdag(Qubit(0))
    builder.CZ(Qubit(0), Qubit(1)).CNOT(Qubit(1), Qubit(0))
    builder.measure(Qubit(0), Bit(0)).measure(Qubit(1), Bit(1))
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert cqasm_v1_string == """version 1.0

qubits 2

prep_z q[0]
prep_z q[1]
i q[0]
x q[0]
y q[0]
z q[0]
rx q[0], 1.234
ry q[0], -1.234
rz q[0], 1.234
x90 q[0]
y90 q[0]
mx90 q[0]
my90 q[0]
s q[0]
sdag q[0]
t q[0]
tdag q[0]
cz q[0], q[1]
cnot q[1], q[0]
measure_z q[0]
measure_z q[1]
"""


@pytest.mark.parametrize(
    "gate",
    [
        BlochSphereRotation(Qubit(0), axis=(1, 1, 1), angle=1.23),
        ControlledGate(Qubit(0), BlochSphereRotation(Qubit(1), axis=(1, 1, 1), angle=1.23)),
        MatrixGate(np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]), [Qubit(0), Qubit(1)]),
    ]
)
def test_anonymous_gates(gate: Gate) -> None:
    builder = CircuitBuilder(2)
    builder.ir.add_gate(gate)
    with pytest.raises(UnsupportedGateError, match="not supported"):  # noqa: PT012
        qc = builder.to_circuit()
        qc.export(fmt=ExportFormat.CQASM_V1)


def test_comment() -> None:
    builder = CircuitBuilder(3)
    builder.H(Qubit(0))
    builder.comment("My comment")
    builder.Rx(Qubit(0), Float(1.234))
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert cqasm_v1_string == """version 1.0

qubits 3

h q[0]

/* My comment */

rx q[0], 1.234
"""
