from src.Common import ArgType, Parameter
import numpy as np
import math, cmath
from src.Gates import SingleQubitAxisAngleSemantic, MultiQubitMatrixSemantic

TEST_GATES = {
    "h": {
        "signature": (ArgType.QUBIT,),
        "semantic": SingleQubitAxisAngleSemantic(axis = (1, 0, 1), angle = math.pi, phase = math.pi / 2),
    },
    "H": "h", # This is how you define an alias.
    "x": {
        "signature": (ArgType.QUBIT,),
        "semantic": SingleQubitAxisAngleSemantic(axis = (1, 0, 0), angle = math.pi, phase = math.pi / 2),
    },
    "X": "x",
    "y": {
        "signature": (ArgType.QUBIT,),
        "semantic": SingleQubitAxisAngleSemantic(axis = (0, 1, 0), angle = math.pi, phase = math.pi / 2),
    },
    "Y": "y",
    "z": {
        "signature": (ArgType.QUBIT,),
        "semantic": SingleQubitAxisAngleSemantic(axis = (0, 0, 1), angle = math.pi, phase = math.pi / 2),
    },
    "Z": "z",
    "rx": {
        "signature": (ArgType.QUBIT, ArgType.FLOAT),
        "semantic": lambda theta: SingleQubitAxisAngleSemantic(axis = (1, 0, 0), angle = theta, phase = 0),
    },
    "RX": "rx",
    "x90": {
        "signature": (ArgType.QUBIT,),
        "semantic": SingleQubitAxisAngleSemantic(axis = (1, 0, 0), angle = math.pi / 2, phase = 0),
    },
    "X90": "x90",
    "mx90": {
        "signature": (ArgType.QUBIT,),
        "semantic": SingleQubitAxisAngleSemantic(axis = (1, 0, 0), angle = - math.pi / 2, phase = 0),
    },
    "MX90": "mx90",
    "ry": {
        "signature": (ArgType.QUBIT, ArgType.FLOAT),
        "semantic": lambda theta: SingleQubitAxisAngleSemantic(axis = (0, 1, 0), angle = theta, phase = 0),
    },
    "RY": "ry",
    "y90": {
        "signature": (ArgType.QUBIT,),
        "semantic": SingleQubitAxisAngleSemantic(axis = (0, 1, 0), angle = math.pi / 2, phase = 0),
    },
    "Y90": "y90",
    "rz": {
        "signature": (ArgType.QUBIT, ArgType.FLOAT),
        "semantic": lambda theta: SingleQubitAxisAngleSemantic(axis = (0, 0, 1), angle = theta, phase = 0),
    },
    "RZ": "rz",
    "cnot": {
        "signature": (ArgType.QUBIT, ArgType.QUBIT),
        "semantic": MultiQubitMatrixSemantic(np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ])),
    },
    "CNOT": "cnot",
    "cz": {
        "signature": (ArgType.QUBIT, ArgType.QUBIT),
        "semantic": MultiQubitMatrixSemantic(np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, -1],
        ])),
    },
    "CZ": "cz",
    "cr": {
        "signature": (ArgType.QUBIT, ArgType.QUBIT, ArgType.FLOAT),
        "semantic": lambda theta: MultiQubitMatrixSemantic(np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, cmath.rect(1, theta)],
        ])),
    },
    "CR": "cr",

    # Rest is TODO
}
