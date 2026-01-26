class TestABADecomposer:
    def test_example_circuit(self) -> None:
        import math

        from opensquirrel.circuit_builder import CircuitBuilder
        from opensquirrel.passes.decomposer import ZYZDecomposer

        builder = CircuitBuilder(qubit_register_size=1)
        builder.H(0).Z(0).Y(0).Rx(0, math.pi / 3)
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
