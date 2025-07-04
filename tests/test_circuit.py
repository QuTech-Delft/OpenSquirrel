from opensquirrel import CircuitBuilder
from opensquirrel.ir import AsmDeclaration


def test_asm_filter() -> None:
    builder = CircuitBuilder(2)
    builder.asm("BackendTest_1", """backend code""")  # other name
    builder.H(0)
    builder.asm("TestBackend", """backend code""")  # exact relevant name
    builder.CNOT(0, 1)
    builder.asm("TestBackend_1", """backend code""")  # relevant name variant 1
    builder.CNOT(0, 1)
    builder.asm("testbackend", """backend code""")  # lowercase name
    builder.H(0)
    builder.asm("_TestBackend_2", """backend code""")  # relevant name variant 2
    builder.to_circuit()
    circuit = builder.to_circuit()

    asm_statements = [statement for statement in circuit.ir.statements if isinstance(statement, AsmDeclaration)]
    assert len(circuit.ir.statements) == 9
    assert len(asm_statements) == 5

    relevant_backend_name = "TestBackend"
    circuit.asm_filter(relevant_backend_name)

    asm_statements = [statement for statement in circuit.ir.statements if isinstance(statement, AsmDeclaration)]
    assert len(circuit.ir.statements) == 7
    assert len(asm_statements) == 3

    for statement in asm_statements:
        assert relevant_backend_name in str(statement.backend_name)
