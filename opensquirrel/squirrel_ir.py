import inspect
from abc import ABC
from dataclasses import dataclass
from functools import wraps
from typing import Callable, List, Optional, Tuple

import numpy as np

from opensquirrel.common import ATOL, normalize_angle, normalize_axis


class SquirrelIRVisitor(ABC):
    def visit_comment(self, comment: "Comment"):
        pass

    def visit_int(self, i: "Int"):
        pass

    def visit_float(self, f: "Float"):
        pass

    def visit_qubit(self, qubit: "Qubit"):
        pass

    def visit_gate(self, gate: "Gate"):
        pass

    def visit_bloch_sphere_rotation(self, bloch_sphere_rotation: "BlochSphereRotation"):
        pass

    def visit_matrix_gate(self, matrix_gate: "MatrixGate"):
        pass

    def visit_controlled_gate(self, controlled_gate: "ControlledGate"):
        pass


class IRNode(ABC):
    def accept(self, visitor: SquirrelIRVisitor):
        pass


class Expression(IRNode, ABC):
    pass


@dataclass
class Float(Expression):
    value: float

    def accept(self, visitor: SquirrelIRVisitor):
        return visitor.visit_float(self)


@dataclass
class Int(Expression):
    value: int

    def accept(self, visitor: SquirrelIRVisitor):
        return visitor.visit_int(self)


@dataclass
class Qubit(Expression):
    index: int

    def __hash__(self):
        return hash(self.index)

    def __repr__(self):
        return f"Qubit[{self.index}]"

    def accept(self, visitor: SquirrelIRVisitor):
        return visitor.visit_qubit(self)


class Statement(IRNode, ABC):
    pass


class Gate(Statement, ABC):
    arguments: Optional[Tuple[Expression, ...]] = None
    generator: Optional[Callable[..., "Gate"]] = None

    @property
    def name(self) -> Optional[str]:
        return self.generator.__name__ if self.generator else None

    @property
    def is_anonymous(self) -> bool:
        return self.arguments is None


class BlochSphereRotation(Gate):
    generator: Optional[Callable[..., "BlochSphereRotation"]] = None

    def __init__(self, qubit: Qubit, axis: Tuple[float, float, float], angle: float, phase: float = 0):
        self.qubit: Qubit = qubit
        self.axis = normalize_axis(np.array(axis).astype(np.float64))
        self.angle = normalize_angle(angle)
        self.phase = normalize_angle(phase)

    def __repr__(self):
        return f"BlochSphereRotation({self.qubit}, axis={self.axis}, angle={self.angle}, phase={self.phase})"

    def __eq__(self, other):
        if self.qubit != other.qubit:
            return False

        if abs(self.phase - other.phase) > ATOL:
            return False

        if np.allclose(self.axis, other.axis):
            return abs(self.angle - other.angle) < ATOL
        elif np.allclose(self.axis, -other.axis):
            return abs(self.angle + other.angle) < ATOL
        return False

    def accept(self, visitor: SquirrelIRVisitor):
        visitor.visit_gate(self)
        return visitor.visit_bloch_sphere_rotation(self)


class MatrixGate(Gate):
    generator: Optional[Callable[..., "MatrixGate"]] = None

    def __init__(self, matrix: np.ndarray, operands: List[Qubit]):
        assert len(operands) >= 2, "For 1q gates, please use BlochSphereRotation"
        assert matrix.shape == (1 << len(operands), 1 << len(operands))

        self.matrix = matrix
        self.operands = operands

    def __eq__(self, other):
        # TODO: Determine whether we shall allow for a global phase difference here.
        return np.allclose(self.matrix, other.matrix)

    def __repr__(self):
        return f"MatrixGate(qubits={self.operands}, matrix={self.matrix})"

    def accept(self, visitor: SquirrelIRVisitor):
        visitor.visit_gate(self)
        return visitor.visit_matrix_gate(self)


class ControlledGate(Gate):
    generator: Optional[Callable[..., "ControlledGate"]] = None

    def __init__(self, control_qubit: Qubit, target_gate: Gate):
        self.control_qubit = control_qubit
        self.target_gate = target_gate

    def __eq__(self, other):
        if self.control_qubit != other.control_qubit:
            return False

        return self.target_gate == other.target_gate

    def __repr__(self):
        return f"ControlledGate(control_qubit={self.control_qubit}, {self.target_gate})"

    def accept(self, visitor: SquirrelIRVisitor):
        visitor.visit_gate(self)
        return visitor.visit_controlled_gate(self)


def named_gate(gate_generator: Callable[..., Gate]) -> Callable[..., Gate]:
    @wraps(gate_generator)
    def wrapper(*args):
        for i, par in enumerate(inspect.signature(gate_generator).parameters.values()):
            if not issubclass(par.annotation, Expression):
                raise TypeError("Gate argument types must be expressions")

        result = gate_generator(*args)
        result.generator = gate_generator
        result.arguments = args
        return result

    return wrapper


@dataclass
class Comment(Statement):
    str: str

    def __post_init__(self):
        assert "*/" not in self.str, "Comment contains illegal characters"

    def accept(self, visitor: SquirrelIRVisitor):
        return visitor.visit_comment(self)


class SquirrelIR:
    # This is just a list of gates (for now?)
    def __init__(self, *, number_of_qubits: int, qubit_register_name: str = "q"):
        self.number_of_qubits: int = number_of_qubits
        self.statements: List[Statement] = []
        self.qubit_register_name: str = qubit_register_name

    def add_gate(self, gate: Gate):
        self.statements.append(gate)

    def add_comment(self, comment: Comment):
        self.statements.append(comment)

    def __eq__(self, other):
        if self.number_of_qubits != other.number_of_qubits:
            return False

        if self.qubit_register_name != other.qubit_register_name:
            return False

        return self.statements == other.statements

    def __repr__(self):
        return f"""IR ({self.number_of_qubits} qubits, register {self.qubit_register_name}): {self.statements}"""

    def accept(self, visitor: SquirrelIRVisitor):
        for statement in self.statements:
            statement.accept(visitor)
