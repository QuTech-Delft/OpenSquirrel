import math

import pytest

from opensquirrel import Circuit, CircuitBuilder, H, I, Rx, Ry, X, Y, Z
from opensquirrel.ir import BlochSphereRotation, Float
from opensquirrel.passes.merger.general_merger import compose_bloch_sphere_rotations, rearrange_barriers


def test_compose_bloch_sphere_rotations_same_axis() -> None:
    a = BlochSphereRotation(qubit=123, axis=(1, 2, 3), angle=0.4)
    b = BlochSphereRotation(qubit=123, axis=(1, 2, 3), angle=-0.3)
    composed = compose_bloch_sphere_rotations(a, b)
    assert composed == BlochSphereRotation(qubit=123, axis=(1, 2, 3), angle=0.1)


def test_compose_bloch_sphere_rotations_different_axis() -> None:
    # Visualizing this in 3D is difficult...
    a = BlochSphereRotation(qubit=123, axis=(1, 0, 0), angle=math.pi / 2)
    b = BlochSphereRotation(qubit=123, axis=(0, 0, 1), angle=-math.pi / 2)
    c = BlochSphereRotation(qubit=123, axis=(0, 1, 0), angle=math.pi / 2)
    composed = compose_bloch_sphere_rotations(compose_bloch_sphere_rotations(c, b), a)
    assert composed == BlochSphereRotation(qubit=123, axis=(1, 1, 0), angle=math.pi)


@pytest.mark.parametrize(
    ("bsr_a", "bsr_b", "expected_result"),
    [
        (Y(0), X(0), BlochSphereRotation(0, axis=(0, 0, 1), angle=math.pi, phase=math.pi)),
        (X(0), Y(0), BlochSphereRotation(0, axis=(0, 0, -1), angle=math.pi, phase=math.pi)),
        (Z(0), Y(0), BlochSphereRotation(0, axis=(1, 0, 0), angle=math.pi, phase=math.pi)),
        (Y(0), Z(0), BlochSphereRotation(0, axis=(-1, 0, 0), angle=math.pi, phase=math.pi)),
        (Z(0), X(0), BlochSphereRotation(0, axis=(0, -1, 0), angle=math.pi, phase=math.pi)),
        (X(0), Z(0), BlochSphereRotation(0, axis=(0, 1, 0), angle=math.pi, phase=math.pi)),
        (
            Rx(0, theta=math.pi),
            Ry(0, theta=-math.pi / 2),
            BlochSphereRotation(0, axis=(0.70711, 0.0, 0.70711), angle=math.pi, phase=0.0),
        ),
        (I(0), Rx(0, theta=math.pi), Rx(0, theta=math.pi)),
        (Rx(0, theta=math.pi), I(0), Rx(0, theta=math.pi)),
        (X(0), X(0), I(0)),
        (H(0), H(0), I(0)),
        (Rx(0, theta=math.pi), Rx(0, theta=math.pi), I(0)),
        (Rx(0, theta=math.pi / 2), Rx(0, theta=math.pi / 2), Rx(0, theta=math.pi)),
    ],
    ids=[
        "[bsr_a = Y, bsr_b = X] X * Y = iZ",
        "[bsr_a = X, bsr_b = Y] Y * X = -iZ",
        "[bsr_a = Z, bsr_b = Y] Y * Z = iX",
        "[bsr_a = Y, bsr_b = Z] Z * Y = -iX",
        "[bsr_a = Z, bsr_b = X] X * Z = -iY",
        "[bsr_a = X, bsr_b = Z] Z * X = iY",
        "[bsr_a = Rx(pi), bsr_b = Ry(-pi/2)] Ry(-pi/2) * Rx(pi) ~ H",
        "[bsr_a == I]",
        "[bsr_b == I]",
        "[bsr_a.generator == bsr_b.generator] X * X == I",
        "[bsr_a.generator == bsr_b.generator] H * H == I",
        "[bsr_a.generator == bsr_b.generator] Rx(pi) * Rx(pi) == I",
        "[bsr_a.generator == bsr_b.generator] Rx(pi/2) * Rx(pi/2) = Rx(pi) ~ X",
    ],
)
def test_compose_bloch_sphere_rotations(
    bsr_a: BlochSphereRotation, bsr_b: BlochSphereRotation, expected_result: BlochSphereRotation
) -> None:
    assert compose_bloch_sphere_rotations(bsr_a, bsr_b) == expected_result


@pytest.mark.parametrize(
    ("circuit", "expected_result"),
    [
        (
            CircuitBuilder(2).H(0).barrier(0).H(1).barrier(1).H(0).Rx(0, Float(math.pi / 3)).barrier(0).to_circuit(),
            """version 3.0

qubit[2] q

H q[0]
H q[1]
barrier q[0]
H q[0]
Rx(1.0471976) q[0]
barrier q[1]
barrier q[0]
""",
        ),
        (
            CircuitBuilder(2).X(0).barrier(0).X(1).barrier(1).CNOT(0, 1).barrier(1).X(1).to_circuit(),
            """version 3.0

qubit[2] q

X q[0]
X q[1]
barrier q[0]
barrier q[1]
CNOT q[0], q[1]
barrier q[1]
X q[1]
""",
        ),
        (
            CircuitBuilder(2).X(0).X(1).barrier(0).barrier(1).X(0).to_circuit(),
            """version 3.0

qubit[2] q

X q[0]
X q[1]
barrier q[0]
barrier q[1]
X q[0]
""",
        ),
        (
            CircuitBuilder(4)
            .H(0)
            .barrier(0)
            .H(1)
            .barrier(1)
            .H(2)
            .barrier(2)
            .H(3)
            .barrier(3)
            .CNOT(0, 3)
            .barrier(0)
            .barrier(1)
            .barrier(3)
            .to_circuit(),
            """version 3.0

qubit[4] q

H q[0]
H q[1]
H q[2]
H q[3]
barrier q[0]
barrier q[1]
barrier q[2]
barrier q[3]
CNOT q[0], q[3]
barrier q[0]
barrier q[1]
barrier q[3]
""",
        ),
    ],
    ids=[
        "anonymous_gate",
        "CNOT_cannot_go_through_a_group_of_linked_barriers",
        "X_cannot_go_through_a_group_of_linked_barriers",
        "circuit_with_4_qubits",
    ],
)
def test_rearrange_barriers(circuit: Circuit, expected_result: str) -> None:
    rearrange_barriers(circuit.ir)
    assert str(circuit) == expected_result
