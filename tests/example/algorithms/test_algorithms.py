"""
Tests for algorithm circuit examples.
I verify that each circuit loads correctly and has expected properties.
"""

from pathlib import Path
from opensquirrel import Circuit

ALGORITHMS_DIR = Path(__file__).parent.parent.parent.parent / "example" / "algorithms"


def load(filename):
    return Circuit.from_string((ALGORITHMS_DIR / filename).read_text())


def test_qft():
    c = load("qft_8.qasm")
    assert c.qubit_register_size == 8
    assert sum(c.instruction_count.values()) > 0


def test_grover():
    c = load("grover_n3.qasm")
    assert c.qubit_register_size == 3
    assert sum(c.instruction_count.values()) > 0


def test_qaoa():
    c = load("qaoa_n6.qasm")
    assert c.qubit_register_size == 6
    assert sum(c.instruction_count.values()) > 0


def test_vqe():
    c = load("vqe_uccsd_n4.qasm")
    assert c.qubit_register_size == 4
    assert sum(c.instruction_count.values()) > 0


def test_benchmark():
    c = load("16QBT_10CYC_TFL_1.qasm")
    assert c.qubit_register_size == 16
    assert sum(c.instruction_count.values()) > 0