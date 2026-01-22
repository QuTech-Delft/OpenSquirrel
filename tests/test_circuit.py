import pytest

from opensquirrel import CircuitBuilder
from opensquirrel.circuit import MeasurementToBitMap
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


def test_instruction_count() -> None:
    builder = CircuitBuilder(2)
    builder.H(0)
    builder.CNOT(0, 1)
    circuit = builder.to_circuit()
    counts = circuit.instruction_count
    assert counts == {"H": 1, "CNOT": 1}

    # non-unitaries
    builder = CircuitBuilder(2, bit_register_size=2)
    builder.barrier(1)
    builder.init(0)
    builder.measure(0, 0)
    circuit = builder.to_circuit()
    counts = circuit.instruction_count
    assert counts == {"barrier": 1, "init": 1, "measure": 1}

    # asm statements
    builder = CircuitBuilder(2)
    builder.barrier(0)
    builder.asm("asm_name", "asm_code")
    builder.barrier(1)
    circuit = builder.to_circuit()
    counts = circuit.instruction_count
    assert counts == {"barrier": 2}


@pytest.mark.parametrize(
    ("builder", "m2b_mapping"),
    [
        (
            CircuitBuilder(3, 3).X(0).Y(1).Z(2),
            {},
        ),
        (
            CircuitBuilder(3, 3).measure(0, 2).measure(2, 0),
            {"0": [2], "2": [0]},
        ),
        (
            CircuitBuilder(3, 3).measure(2, 2).measure(1, 2).measure(0, 2),
            {"0": [2], "1": [2], "2": [2]},
        ),
        (
            CircuitBuilder(3, 3).measure(1, 1).measure(0, 0).measure(1, 1).measure(0, 0),
            {"0": [0, 0], "1": [1, 1]},
        ),
        (
            CircuitBuilder(3, 3).X(0).measure(0, 0).X(1).measure(1, 1).X(2).measure(2, 0).X(0).measure(0, 2),
            {"0": [0, 2], "1": [1], "2": [0]},
        ),
    ],
    ids=["no_measurement", "no_measurement_on_1_qubit", "overwriting_bit_1", "overwriting_bit_2", "example_circuit"],
)
def test_measurement_to_bit_mapping(builder: CircuitBuilder, m2b_mapping: MeasurementToBitMap) -> None:
    circuit = builder.to_circuit()
    assert circuit.measurement_to_bit_map == m2b_mapping
