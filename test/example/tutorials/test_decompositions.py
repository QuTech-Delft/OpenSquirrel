import math

import sympy as sp
from IPython.display import display

from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.default_gates import H, Rx, Rz
from opensquirrel.decomposer.aba_decomposer import ZYZDecomposer, XZXDecomposer
from opensquirrel.decomposer.cnot_decomposer import CNOTDecomposer
from opensquirrel.decomposer.mckay_decomposer import McKayDecomposer
from opensquirrel.ir import Float, Qubit


class TestDecomposition:
    def test_sympy_disp(self):

        theta1, theta2, theta3 = sp.symbols("theta_1 theta_2 theta_3")

        z1 = sp.algebras.Quaternion.from_axis_angle((0, 0, 1), theta1)
        y = sp.algebras.Quaternion.from_axis_angle((0, 1, 0), theta2)
        z2 = sp.algebras.Quaternion.from_axis_angle((0, 0, 1), theta3)

        rhs = sp.trigsimp(sp.expand(z1 * y * z2))

        p, m = sp.symbols("p m")

        rhs_simplified = rhs.subs({theta1 + theta3: p, theta1 - theta3: m})

        alpha, nx, ny, nz = sp.symbols("alpha n_x n_y n_z")

        q = sp.algebras.Quaternion.from_axis_angle((nx, ny, nz), alpha).subs(
            {nx**2 + ny**2 + nz**2: 1}  # We assume the axis is normalized.
        )

        display(
            sp.Eq(rhs_simplified.a, q.a),
            sp.Eq(rhs_simplified.b, q.b),
            sp.Eq(rhs_simplified.c, q.c),
            sp.Eq(rhs_simplified.d, q.d),
        )

        sp.trigsimp(sp.Eq(rhs_simplified.a, q.a).subs(sp.cos(theta2 / 2), nz * sp.sin(alpha / 2) / sp.sin(p / 2)))

        theta1, theta2, theta3 = sp.symbols("theta_1 theta_2 theta_3")

        y1 = sp.algebras.Quaternion.from_axis_angle((0, 1, 0), theta1)
        z = sp.algebras.Quaternion.from_axis_angle((0, 0, 1), theta2)
        y2 = sp.algebras.Quaternion.from_axis_angle((0, 1, 0), theta3)

        rhs = sp.trigsimp(sp.expand(y1 * z * y2))
        rhs_string = "cos(theta_2/2)*cos((theta_1 + theta_3)/2) + sin(theta_2/2)*sin((theta_1 - theta_3)/2)*i + sin((theta_1 + theta_3)/2)*cos(theta_2/2)*j + sin(theta_2/2)*cos((theta_1 - theta_3)/2)*k"
        assert str(rhs) == rhs_string

    def test_builder_ABA(self):

        builder = CircuitBuilder(qubit_register_size=1)
        # Add Hadamard to the circuit
        builder.H(Qubit(0))

        # Add Z to the circuit
        builder.Z(Qubit(0))

        # Add Y to the circuit
        builder.Y(Qubit(0))

        # Add a pi/3 rotation in the X axis to the circuit
        builder.Rx(Qubit(0), Float(math.pi / 3))

        # Convert the builder object into a circuit
        circuit = builder.to_circuit()
        assert (
            str(circuit)
            == """version 3.0

qubit[1] q

H q[0]
Z q[0]
Y q[0]
Rx(1.0471976) q[0]
"""
        )

    def test_zyz_decomposer(self):

        builder = CircuitBuilder(qubit_register_size=1)
        # Add Hadamard to the circuit
        builder.H(Qubit(0))

        # Add Z to the circuit
        builder.Z(Qubit(0))

        # Add Y to the circuit
        builder.Y(Qubit(0))

        # Add a pi/3 rotation in the X axis to the circuit
        builder.Rx(Qubit(0), Float(math.pi / 3))

        # Convert the builder object into a circuit
        circuit = builder.to_circuit()
        circuit.decompose(decomposer=ZYZDecomposer())

        assert (
            str(circuit)
            == """version 3.0

qubit[1] q

Rz(3.1415927) q[0]
Ry(1.5707963) q[0]
Rz(3.1415927) q[0]
Ry(3.1415927) q[0]
Rz(1.5707963) q[0]
Ry(1.0471976) q[0]
Rz(-1.5707963) q[0]
"""
        )
        assert (
            XZXDecomposer().decompose(H(Qubit(0)))
            == [Rx(Qubit(0), Float(math.pi/2)), Rz(Qubit(0), Float(math.pi/2)), Rx(Qubit(0), Float(math.pi/2))]
        )

    def test_builder_and_mckay(self):
        builder = CircuitBuilder(qubit_register_size=1)
        # Add Hadamard to the circuit
        builder.H(Qubit(0))

        # Add Z to the circuit
        builder.Z(Qubit(0))

        # Add X to the circuit
        builder.X(Qubit(0))

        # Add a pi/3 rotation in the X axis to the circuit
        builder.Rx(Qubit(0), Float(math.pi / 3))

        # Convert the builder object into a circuit
        circuit = builder.to_circuit()

        assert (
            str(circuit)
            == """version 3.0

qubit[1] q

H q[0]
Z q[0]
X q[0]
Rx(1.0471976) q[0]
"""
        )
        circuit.decompose(decomposer=McKayDecomposer())
        assert (
            str(circuit)
            == """version 3.0

qubit[1] q

Rz(1.5707963) q[0]
X90 q[0]
Rz(1.5707963) q[0]
Rz(3.1415927) q[0]
X90 q[0]
X90 q[0]
Rz(-1.5707963) q[0]
X90 q[0]
Rz(2.0943951) q[0]
X90 q[0]
Rz(-1.5707963) q[0]
"""
        )

    def test_builder_and_cnot(self):
        builder = CircuitBuilder(qubit_register_size=2)
        # Add Hadamard to the circuit
        builder.CZ(Qubit(0), Qubit(1))

        # Add Hadamard to the circuit
        builder.CR(Qubit(0), Qubit(1), Float(math.pi / 3))

        # Add Hadamard to the circuit
        builder.CR(Qubit(1), Qubit(0), Float(math.pi / 2))

        # Convert the builder object into a circuit
        circuit = builder.to_circuit()

        assert (
            str(circuit)
            == """version 3.0

qubit[2] q

CZ q[0], q[1]
CR(1.0471976) q[0], q[1]
CR(1.5707963) q[1], q[0]
"""
        )
        circuit.decompose(decomposer=CNOTDecomposer())
        assert (
            str(circuit)
            == """version 3.0

qubit[2] q

Rz(-3.1415927) q[1]
Ry(1.5707963) q[1]
CNOT q[0], q[1]
Ry(-1.5707963) q[1]
Rz(3.1415927) q[1]
Rz(0.52359878) q[1]
CNOT q[0], q[1]
Rz(-0.52359878) q[1]
CNOT q[0], q[1]
Rz(0.52359878) q[0]
Rz(0.78539816) q[0]
CNOT q[1], q[0]
Rz(-0.78539816) q[0]
CNOT q[1], q[0]
Rz(0.78539816) q[1]
"""
        )
