import pytest

from opensquirrel.default_gates import CNOT, H
from opensquirrel.mapper import HardcodedMapper, Mapper, map_qubits
from opensquirrel.squirrel_ir import Comment, Measure, Qubit, SquirrelIR


class TestMapper:

    def test_init(self) -> None:
        with pytest.raises(TypeError):
            Mapper()

    def test_implementation(self) -> None:

        class Mapper2(Mapper):
            pass

        with pytest.raises(TypeError):
            Mapper2()

        class Mapper3(Mapper2):
            def map(self, squirrel_ir: SquirrelIR) -> dict[int, int]:
                return {0: 0}

        Mapper3()


def test_map_qubits() -> None:
    # Build the IR
    squirrel_ir = SquirrelIR(number_of_qubits=3)
    squirrel_ir.add_gate(H(Qubit(0)))
    squirrel_ir.add_gate(CNOT(Qubit(0), Qubit(1)))
    squirrel_ir.add_gate(CNOT(Qubit(1), Qubit(2)))
    squirrel_ir.add_comment(Comment("Qubit[1]"))
    squirrel_ir.add_measurement(Measure(Qubit(0), axis=(0, 0, 1)))

    # Map the circuit
    mapper = HardcodedMapper({0: 1, 1: 0, 2: 2})
    map_qubits(squirrel_ir, mapper)

    # Check that the circuit is altered as expected
    mapped_statements = squirrel_ir.statements
    expected_statements = [
        H(Qubit(1)),
        CNOT(Qubit(1), Qubit(0)),
        CNOT(Qubit(0), Qubit(2)),
        Comment("Qubit[1]"),
        Measure(Qubit(1), axis=(0, 0, 1)),
    ]
    assert mapped_statements == expected_statements
