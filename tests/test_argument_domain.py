from opensquirrel import Circuit, CircuitBuilder


def test_argument_domain():

    circuit = Circuit.from_string(
        """
        version 3.0

        qubit[2] q

        pow(2).Rx(2) q[0]
        Rn(0.1,0.1,0.1,tau,tau/2+0.0001) q[1]
        CR(tau + pi) q[0], q[1]
        CRk(2) q[0], q[1]
        """
    )

    print(circuit)

    for statement in circuit.ir.statements:
        print(statement)


def test_argument_domain_builder():
    import math

    builder = CircuitBuilder(2)
    builder.Rx(0, math.tau)
    builder.Rn(0, 1, 1, 1, math.tau, math.tau/2 + 0.000_01)
    builder.CR(0, 1, math.tau)
    builder.CRk(0, 1, 2)

    circuit = builder.to_circuit()

    print(circuit)

    for statement in circuit.ir.statements:
        print(statement)
