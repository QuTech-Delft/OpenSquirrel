from opensquirrel.circuit import Circuit
from opensquirrel.circuit_builder import CircuitBuilder
from opensquirrel.ir import (
    Barrier,
    Init,
    Measure,
    Reset,
    Wait,
)
from opensquirrel.ir.default_gates import (
    CNOT,
    CR,
    CZ,
    SWAP,
    X90,
    Y90,
    CRk,
    H,
    I,
    MinusX90,
    MinusY90,
    Rn,
    Rx,
    Ry,
    Rz,
    S,
    SDagger,
    T,
    TDagger,
    X,
    Y,
    Z,
)

__all__ = [
    "CNOT",
    "CR",
    "CZ",
    "SWAP",
    "X90",
    "Y90",
    "Barrier",
    "CRk",
    "Circuit",
    "CircuitBuilder",
    "H",
    "I",
    "Init",
    "Measure",
    "MinusX90",
    "MinusY90",
    "Reset",
    "Rn",
    "Rx",
    "Ry",
    "Rz",
    "S",
    "SDagger",
    "T",
    "TDagger",
    "Wait",
    "X",
    "Y",
    "Z",
]

from importlib.metadata import version

__version__ = version("opensquirrel")
