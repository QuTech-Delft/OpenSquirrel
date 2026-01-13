from math import pi

import pytest

from opensquirrel import Circuit, CircuitBuilder
from opensquirrel.exceptions import UnsupportedGateError
from opensquirrel.ir import Gate
from opensquirrel.ir.semantics import BlochSphereRotation, ControlledGateSemantic, MatrixGateSemantic
from opensquirrel.ir.single_qubit_gate import SingleQubitGate
from opensquirrel.ir.two_qubit_gate import TwoQubitGate
from opensquirrel.passes.exporter import CqasmV1Exporter


@pytest.fixture
def exporter() -> CqasmV1Exporter:
    return CqasmV1Exporter()


def test_cqasm_v3_to_cqasm_v1(exporter: CqasmV1Exporter) -> None:
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
    cqasm_v1_string = cqasm_v3_string.export(exporter=exporter)
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
rx q[0], -1.1601853
measure_z q[0]
measure_z q[1]
"""
    )


def test_version_statement(exporter: CqasmV1Exporter) -> None:
    circuit = Circuit.from_string("""version 3.0""")
    cqasm_v1_string = circuit.export(exporter=exporter)
    assert (
        cqasm_v1_string
        == """version 1.0
"""
    )


def test_qubit_statement(exporter: CqasmV1Exporter) -> None:
    builder = CircuitBuilder(3)
    circuit = builder.to_circuit()
    cqasm_v1_string = circuit.export(exporter=exporter)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 3
"""
    )


def test_circuit_to_string_after_circuit_modification(exporter: CqasmV1Exporter) -> None:
    builder = CircuitBuilder(3)
    circuit = builder.to_circuit()
    cqasm_v1_string = circuit.export(exporter=exporter)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 3
"""
    )

    builder.H(0)
    builder.CNOT(0, 1)
    circuit = builder.to_circuit()
    cqasm_v1_string = circuit.export(exporter=exporter)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 3

h q[0]
cnot q[0], q[1]
"""
    )


def test_float_precision(exporter: CqasmV1Exporter) -> None:
    builder = CircuitBuilder(3)
    builder.Rx(0, 1.6546514861321684321654)
    circuit = builder.to_circuit()
    cqasm_v1_string = circuit.export(exporter=exporter)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 3

rx q[0], 1.6546515
"""
    )


def test_measure(exporter: CqasmV1Exporter) -> None:
    builder = CircuitBuilder(2, 2)
    builder.H(0)
    builder.measure(0, 0)
    builder.measure(0, 1)
    builder.measure(1, 0)
    builder.measure(1, 1)
    circuit = builder.to_circuit()
    cqasm_v1_string = circuit.export(exporter=exporter)
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


def test_init(exporter: CqasmV1Exporter) -> None:
    builder = CircuitBuilder(1, 1)
    builder.init(0)
    builder.H(0)
    circuit = builder.to_circuit()
    cqasm_v1_string = circuit.export(exporter=exporter)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 1

prep_z q[0]
h q[0]
"""
    )


def test_reset(exporter: CqasmV1Exporter) -> None:
    builder = CircuitBuilder(1, 1)
    builder.H(0)
    builder.reset(0)
    circuit = builder.to_circuit()
    cqasm_v1_string = circuit.export(exporter=exporter)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 1

h q[0]
prep_z q[0]
"""
    )


def test_u_gate(exporter: CqasmV1Exporter) -> None:
    builder = CircuitBuilder(1)
    builder.U(0, pi / 2, 0, pi)
    builder.U(0, pi, 0, pi)
    builder.U(0, pi, pi / 2, pi / 2)
    builder.U(0, 0, pi, 0)
    builder.U(0, 1, 2, 3)

    circuit = builder.to_circuit()
    cqasm_v1_string = circuit.export(exporter=exporter)
    assert (
        cqasm_v1_string
        == """version 1.0

qubits 1

u q[0], [0.70711, 0.70711; 0.70711, -0.70711]
u q[0], [0.0, 1.0; 1.0, 0.0]
u q[0], [0.0, -1.0 * im; 1.0 * im, 0.0]
u q[0], [1.0, 0.0; 0.0, -1.0]
u q[0], [0.87758, 0.47463-0.06766 * im; -0.19951+0.43594 * im, 0.24894-0.84154 * im]
"""
    )


def test_all_instructions(exporter: CqasmV1Exporter) -> None:
    builder = CircuitBuilder(2, 2)
    builder.init(0).reset(1).barrier(0).wait(1, 3)
    builder.I(0).X(0).Y(0).Z(0)
    builder.Rx(0, 1.234).Ry(0, -1.234).Rz(0, 1.234)
    builder.X90(0).Y90(0)
    builder.mX90(0).mY90(0)
    builder.S(0).Sdag(0).T(0).Tdag(0)
    builder.CZ(0, 1).CNOT(1, 0).SWAP(0, 1)
    builder.measure(0, 0).measure(1, 1)
    circuit = builder.to_circuit()
    cqasm_v1_string = circuit.export(exporter=exporter)
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
        SingleQubitGate(0, gate_semantic=BlochSphereRotation(axis=(1, 1, 1), angle=1.23, phase=0.0)),
        TwoQubitGate(
            0,
            1,
            gate_semantic=ControlledGateSemantic(
                SingleQubitGate(qubit=1, gate_semantic=BlochSphereRotation(axis=(1, 1, 1), angle=1.23, phase=0.0))
            ),
        ),
        TwoQubitGate(0, 1, gate_semantic=MatrixGateSemantic([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])),
    ],
)
def test_anonymous_gates(exporter: CqasmV1Exporter, gate: Gate) -> None:
    builder = CircuitBuilder(2)
    builder.ir.add_gate(gate)
    with pytest.raises(UnsupportedGateError, match="not supported"):
        circuit = builder.to_circuit()
        circuit.export(exporter=exporter)


@pytest.mark.parametrize(
    ("program", "expected_output"),
    [
        (
            "version 3.0; qubit[1] q; barrier q[0];",
            "version 1.0\n\nqubits 1\n\nbarrier q[0]\n",
        ),
        (
            "version 3.0; qubit[3] q; barrier q[0:2]",
            "version 1.0\n\nqubits 3\n\nbarrier q[0, 1, 2]\n",
        ),
        (
            "version 3.0; qubit[1] q; barrier q[0, 0]",
            "version 1.0\n\nqubits 1\n\nbarrier q[0, 0]\n",
        ),
        (
            "version 3.0; qubit[6] q; barrier q[0:2, 5, 3, 4, 1]",
            "version 1.0\n\nqubits 6\n\nbarrier q[0, 1, 2, 5, 3, 4, 1]\n",
        ),
        (
            "version 3.0; qubit[5] q; barrier q[0]; H q[1]; barrier q[1:2]; X q[2]; barrier q[3:4, 1]; Y q[3];"  # noqa: ISC004
            "barrier q[0]; barrier q[2]",
            "version 1.0\n\nqubits 5\n\nbarrier q[0]\nh q[1]\nbarrier q[1, 2]\nx q[2]\nbarrier q[3, 4, 1]\ny q[3]\n"  # noqa: ISC004
            "barrier q[0, 2]\n",
        ),
        (
            "version 3.0; qubit[3] q; barrier q[0]; barrier q[1]; X q[2]; barrier q[1]; X q[2]",
            "version 1.0\n\nqubits 3\n\nbarrier q[0, 1]\nx q[2]\nbarrier q[1]\nx q[2]\n",
        ),
        (
            "version 3.0; qubit[20] q; barrier q[14]; barrier q[9:12]; X q[2]; barrier q[19]",
            "version 1.0\n\nqubits 20\n\nbarrier q[14, 9, 10, 11, 12]\nx q[2]\nbarrier q[19]\n",
        ),
    ],
    ids=[
        "no_group",
        "single_group",
        "repeated_index",
        "preserve_order",
        "with_instructions",
        "group_consecutive_barriers",
        "double_digit_register_size",
    ],
)
def test_barrier_groups(exporter: CqasmV1Exporter, program: str, expected_output: str) -> None:
    circuit = Circuit.from_string(program)
    output = circuit.export(exporter=exporter)
    assert output == expected_output
