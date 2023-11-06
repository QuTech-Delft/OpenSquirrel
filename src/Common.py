import math, cmath
from enum import Enum
import numpy as np

ATOL = 0.0000001

class ExprType(Enum):
    QUBITREFS = 1
    FLOAT = 2
    INT = 3

class ArgType(Enum):
    QUBIT = 0
    FLOAT = 1
    INT = 2

def exprTypeToArgType(t):
  if t == ExprType.QUBITREFS:
    return ArgType.QUBIT
  if t == ExprType.FLOAT:
    return ArgType.FLOAT
  if t == ExprType.INT:
    return ArgType.INT

class Parameter:
  def __init__(self, n):
    self.value = n

X = np.array([[0, 1], [1, 0]])
Y = np.array([[0, -1j], [1j, 0]])
Z = np.array([[1, 0], [0, -1]])

def Can1(axis, angle, phase = 0):
    nx, ny, nz = axis
    norm = math.sqrt(nx**2 + ny**2 + nz**2)
    assert norm > 0.00000001

    nx /= norm
    ny /= norm
    nz /= norm

    result = cmath.rect(1, phase) * (math.cos(angle / 2) * np.identity(2) - 1j * math.sin(angle / 2) * (nx * X + ny * Y + nz * Z))

    return result
