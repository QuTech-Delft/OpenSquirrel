from pathlib import Path

from opensquirrel import Circuit

ALGORITHMS_DIR = Path(__file__).parent.parent.parent.parent / "example" / "algorithms"


def load(filename: str) -> Circuit:
    return Circuit.from_string((ALGORITHMS_DIR / filename).read_text())


def test_grover() -> None:
    c = load("grover_n3.cq")
    assert c.qubit_register_size == 3
    assert c.instruction_count["H"] == 23
    assert c.instruction_count["CZ"] == 24
    assert c.instruction_count["measure"] == 3
    assert sum(c.instruction_count.values()) == 178


def test_qft() -> None:
    c = load("qft_8.cq")
    assert c.qubit_register_size == 8
    assert c.instruction_count["CNOT"] == 68
    assert c.instruction_count["Rz"] == 100
    assert c.instruction_count["measure"] == 8
    assert sum(c.instruction_count.values()) == 184


def test_qaoa() -> None:
    c = load("qaoa_n6.cq")
    assert c.qubit_register_size == 6
    assert c.instruction_count["H"] == 6
    assert c.instruction_count["CNOT"] == 54
    assert c.instruction_count["Rx"] == 66
    assert c.instruction_count["measure"] == 6
    assert sum(c.instruction_count.values()) == 377


def test_vqe() -> None:
    c = load("vqe_uccsd_n4.cq")
    assert c.qubit_register_size == 4
    assert c.instruction_count["H"] == 56
    assert c.instruction_count["CNOT"] == 88
    assert c.instruction_count["measure"] == 4
    assert sum(c.instruction_count.values()) == 224


def test_benchmark() -> None:
    c = load("16QBT_10CYC_TFL_1.cq")
    assert c.qubit_register_size == 16
    assert set(c.instruction_count.keys()) == {"X", "CNOT", "measure"}
    assert c.instruction_count["X"] == 44
    assert c.instruction_count["CNOT"] == 29
    assert c.instruction_count["measure"] == 16
    assert sum(c.instruction_count.values()) == 89