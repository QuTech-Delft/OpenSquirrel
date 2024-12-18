import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.exceptions import UnsupportedGateError
from opensquirrel.ir import BlochSphereRotation, ControlledGate, Gate, MatrixGate
from opensquirrel.passes.exporter import ExportFormat


def test_cqasm_v3_to_cqasm_v1() -> None:
    cqasm_v3_string = Circuit.from_string(
        """
    version 3.0

    qubit[2] q
    bit[2] b

    init q
    I q[0]
    barrier q[1]
    H q[0]
    reset q
    CNOT q[0], q[1]
    wait(3) q
    Rx(5.123) q[0]
    b = measure q
    """
    )
    cqasm_v1_string = cqasm_v3_string.export(fmt=ExportFormat.CQASM_V1)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 2

prep_z q[0]
prep_z q[1]
i q[0]
barrier q[1]
h q[0]
prep_z q[0]
prep_z q[1]
cnot q[0], q[1]
wait q[0], 3
wait q[1], 3
rx q[0], 5.123
measure_z q[0]
measure_z q[1]
"""
    )


def test_version_statement() -> None:
    qc = Circuit.from_string("""version 3.0""")
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert (
        cqasm_v1_string
        == """version 1.0
"""
    )


def test_qubit_statement() -> None:
    builder = CircuitBuilder(3)
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 3
"""
    )


def test_circuit_to_string_after_circuit_modification() -> None:
    builder = CircuitBuilder(3)
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 3
"""
    )

    builder.H(0)
    builder.CNOT(0, 1)
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 3

h q[0]
cnot q[0], q[1]
"""
    )


def test_float_precision() -> None:
    builder = CircuitBuilder(3)
    builder.Rx(0, 1.6546514861321684321654)
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 3

rx q[0], 1.6546515
"""
    )


def test_measure() -> None:
    builder = CircuitBuilder(2, 2)
    builder.H(0)
    builder.measure(0, 0)
    builder.measure(0, 1)
    builder.measure(1, 0)
    builder.measure(1, 1)
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 2

h q[0]
measure_z q[0]
measure_z q[0]
measure_z q[1]
measure_z q[1]
"""
    )


def test_init() -> None:
    builder = CircuitBuilder(1, 1)
    builder.init(0)
    builder.H(0)
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 1

prep_z q[0]
h q[0]
"""
    )


def test_reset() -> None:
    builder = CircuitBuilder(1, 1)
    builder.H(0)
    builder.reset(0)
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 1

h q[0]
prep_z q[0]
"""
    )


def test_all_instructions() -> None:
    builder = CircuitBuilder(2, 2)
    builder.init(0).reset(1).barrier(0).wait(1, 3)
    builder.I(0).X(0).Y(0).Z(0)
    builder.Rx(0, 1.234).Ry(0, -1.234).Rz(0, 1.234)
    builder.X90(0).Y90(0)
    builder.mX90(0).mY90(0)
    builder.S(0).Sdag(0).T(0).Tdag(0)
    builder.CZ(0, 1).CNOT(1, 0).SWAP(0, 1)
    builder.measure(0, 0).measure(1, 1)
    qc = builder.to_circuit()
    cqasm_v1_string = qc.export(fmt=ExportFormat.CQASM_V1)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 2

prep_z q[0]
prep_z q[1]
barrier q[0]
wait q[1], 3
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
swap q[0], q[1]
measure_z q[0]
measure_z q[1]
"""
    )


@pytest.mark.parametrize(
    "gate",
    [
        BlochSphereRotation(0, axis=(1, 1, 1), angle=1.23),
        ControlledGate(0, BlochSphereRotation(1, axis=(1, 1, 1), angle=1.23)),
        MatrixGate([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], [0, 1]),
    ],
)
def test_anonymous_gates(gate: Gate) -> None:
    builder = CircuitBuilder(2)
    builder.ir.add_gate(gate)
    with pytest.raises(UnsupportedGateError, match="not supported"):  # noqa: PT012
        qc = builder.to_circuit()
        qc.export(fmt=ExportFormat.CQASM_V1)
