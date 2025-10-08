import math

import pytest

from opensquirrel import Circuit, CircuitBuilder, Rn
from opensquirrel.ir.semantics import BlochSphereRotation
from opensquirrel.passes.merger import SingleQubitGatesMerger
from opensquirrel.passes.merger.general_merger import rearrange_barriers
from tests.ir.ir_equality_test_base import modify_circuit_and_check


@pytest.fixture
def merger() -> SingleQubitGatesMerger:
    return SingleQubitGatesMerger()


def test_single_gate(merger: SingleQubitGatesMerger) -> None:
    builder1 = CircuitBuilder(1)
    builder1.Ry(0, 1.2345)
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(1)
    builder2.Ry(0, 1.2345)
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, merger.merge, expected_circuit)


def test_two_hadamards(merger: SingleQubitGatesMerger) -> None:
    builder = CircuitBuilder(4)
    builder.H(2)
    builder.H(2)
    circuit = builder.to_circuit()

    expected_circuit = CircuitBuilder(4).to_circuit()

    modify_circuit_and_check(circuit, merger.merge, expected_circuit)


def test_two_hadamards_different_qubits(merger: SingleQubitGatesMerger) -> None:
    builder1 = CircuitBuilder(4)
    builder1.H(0)
    builder1.H(2)
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.H(0)
    builder2.H(2)
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, merger.merge, expected_circuit)


def test_merge_different_qubits(merger: SingleQubitGatesMerger) -> None:
    builder1 = CircuitBuilder(4)
    builder1.Ry(0, math.pi / 2)
    builder1.Rx(0, math.pi)
    builder1.Rz(1, 1.2345)
    builder1.Ry(2, 1)
    builder1.Ry(2, 3.234)
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.ir.add_gate(Rn(0, 1, 0, 1, math.pi, 0))  # this is Hadamard with 0 phase
    builder2.Rz(1, 1.2345)
    builder2.Ry(2, 4.234)
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, merger.merge, expected_circuit)


def test_merge_and_flush(merger: SingleQubitGatesMerger) -> None:
    builder1 = CircuitBuilder(4)
    builder1.Ry(0, math.pi / 2)
    builder1.Rz(1, 1.5)
    builder1.Rx(0, math.pi)
    builder1.Rz(1, -2.5)
    builder1.CNOT(0, 1)
    builder1.Ry(0, 3.234)
    circuit = builder1.to_circuit()

    builder2 = CircuitBuilder(4)
    builder2.ir.add_gate(BlochSphereRotation(0, axis=(1, 0, 1), angle=math.pi, phase=0.0))
    builder2.Rz(1, -1.0)
    builder2.CNOT(0, 1)
    builder2.Ry(0, 3.234)
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, merger.merge, expected_circuit)


def test_merge_y90_x_to_h(merger: SingleQubitGatesMerger) -> None:
    builder = CircuitBuilder(1)
    builder.Ry(0, math.pi / 2)
    builder.X(0)
    circuit = builder.to_circuit()

    builder2 = CircuitBuilder(1)
    builder2.H(0)
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, merger.merge, expected_circuit)


def test_no_merge_across_measure(merger: SingleQubitGatesMerger) -> None:
    builder = CircuitBuilder(2, 2)
    builder.H(0)
    builder.measure(0, 0)
    builder.H(0)
    builder.H(1)
    builder.measure(0, 1)
    builder.H(1)
    circuit = builder.to_circuit()

    builder2 = CircuitBuilder(2, 2)
    builder2.H(0)
    builder2.measure(0, 0)
    builder2.H(0)
    builder2.measure(0, 1)
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, merger.merge, expected_circuit)


def test_no_merge_across_reset(merger: SingleQubitGatesMerger) -> None:
    builder = CircuitBuilder(2)
    builder.H(0)
    builder.reset(0)
    builder.H(0)
    builder.H(1)
    builder.reset(0)
    builder.H(1)
    circuit = builder.to_circuit()

    builder2 = CircuitBuilder(2)
    builder2.H(0)
    builder2.reset(0)
    builder2.H(0)
    builder2.reset(0)
    expected_circuit = builder2.to_circuit()

    modify_circuit_and_check(circuit, merger.merge, expected_circuit)


def test_no_merge_across_wait(merger: SingleQubitGatesMerger) -> None:
    builder = CircuitBuilder(2)
    builder.H(0)
    builder.wait(0, 3)
    builder.H(0)
    builder.H(1)
    builder.wait(0, 3)
    builder.H(1)
    circuit = builder.to_circuit()

    builder2 = CircuitBuilder(2)
    builder2.H(0)
    builder2.wait(0, 3)
    builder2.H(0)
    builder2.wait(0, 3)
    expected_circuit = builder2.to_circuit()
    modify_circuit_and_check(circuit, merger.merge, expected_circuit)


@pytest.mark.parametrize(
    ("circuit", "expected_result"),
    [
        (
            (
                CircuitBuilder(2)
                .H(1)
                .Rz(1, 2.332)
                .H(0)
                .Rx(0, 1.423)
                .barrier(0)
                .barrier(1)
                .H(1)
                .Rz(1, 2.332)
                .H(0)
                .Rx(1, 1.423)
                .barrier(0)
                .barrier(1)
                .to_circuit()
            ),
            """version 3.0

qubit[2] q

Rn(0.60376021, -0.52052591, 0.60376021, -2.1817262, 1.5707963) q[0]
Rn(0.36643768, 0.85524666, 0.36643768, -1.7265283, 1.5707963) q[1]
barrier q[0]
barrier q[1]
H q[0]
Rn(0.28903179, -0.42027578, -0.86013307, 1.6620774, 1.5707963) q[1]
barrier q[0]
barrier q[1]
""",
        ),
        (
            CircuitBuilder(3)
            .H(0)
            .Ry(0, 2)
            .barrier(2)
            .barrier(0)
            .barrier(1)
            .H(0)
            .H(1)
            .Ry(1, 2)
            .barrier(1)
            .H(2)
            .barrier(2)
            .barrier(0)
            .barrier(1)
            .to_circuit(),
            """version 3.0

qubit[3] q

Rn(0.97706127, 0.0, -0.21295839, 3.1415927, 1.5707963) q[0]
barrier q[2]
barrier q[0]
barrier q[1]
H q[0]
Rn(0.97706127, 0.0, -0.21295839, 3.1415927, 1.5707963) q[1]
H q[2]
barrier q[1]
barrier q[2]
barrier q[0]
barrier q[1]
""",
        ),
        (
            CircuitBuilder(2).H(0).Ry(0, 2).barrier(1).barrier(0).barrier(1).H(0).H(1).Ry(1, 2).barrier(1).to_circuit(),
            """version 3.0

qubit[2] q

Rn(0.97706127, 0.0, -0.21295839, 3.1415927, 1.5707963) q[0]
barrier q[1]
barrier q[0]
barrier q[1]
H q[0]
Rn(0.97706127, 0.0, -0.21295839, 3.1415927, 1.5707963) q[1]
barrier q[1]
""",
        ),
    ],
    ids=["generic_case", "circuit_with_irregular_barrier_order", "repeating_barrier"],
)
def test_rearrange_barriers_after_merge_single_qubit_gates(
    circuit: Circuit, expected_result: str, merger: SingleQubitGatesMerger
) -> None:
    circuit.merge(merger=merger)
    rearrange_barriers(circuit.ir)
    assert str(circuit) == expected_result
