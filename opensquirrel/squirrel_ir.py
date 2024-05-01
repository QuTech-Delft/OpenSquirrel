from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from functools import wraps
from typing import Callable, List, Optional, Tuple

import numpy as np

from opensquirrel.common import ATOL, are_matrices_equivalent_up_to_global_phase, normalize_angle, normalize_axis


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

    def visit_measure(self, measure: "Measure"):
        pass

    def visit_bloch_sphere_rotation(self, bloch_sphere_rotation: "BlochSphereRotation"):
        pass

    def visit_matrix_gate(self, matrix_gate: "MatrixGate"):
        pass

    def visit_controlled_gate(self, controlled_gate: "ControlledGate"):
        pass


class IRNode(ABC):
    @abstractmethod
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


class Measure(Statement, ABC):
    generator: Optional[Callable[..., "Measure"]] = None
    arguments: Optional[Tuple[Expression, ...]] = None

    def __init__(
        self,
        qubit: Qubit,
        axis: Tuple[float, float, float],
        generator=None,
        arguments=None,
    ):
        self.generator = generator
        self.arguments = arguments
        self.qubit: Qubit = qubit
        self.axis = normalize_axis(np.array(axis).astype(np.float64))

    def __repr__(self):
        return f"Measure({self.qubit}, axis={self.axis})"

    @property
    def name(self) -> Optional[str]:
        return self.generator.__name__ if self.generator else "<abstract_measurement>"

    def __eq__(self, other):
        if not isinstance(other, Measure):
            return False
        return self.qubit == other.qubit and np.allclose(self.axis, other.axis, atol=ATOL)

    def accept(self, visitor: SquirrelIRVisitor):
        visitor.visit_measure(self)

    def get_qubit_operands(self) -> List[Qubit]:
        return [self.qubit]

    def relabel(self, mapping: Mapping[int, int]) -> None:
        """Relabel the qubits using the given mapping.

        Args:
            mapping: Mapping from the indices of the original qubits to the indices of the qubits after replacement.
        """
        self.qubit = Qubit(mapping[self.qubit.index])


class Gate(Statement, ABC):
    # Note: two gates are considered equal even when their generators/arguments are different.
    generator: Optional[Callable[..., "Gate"]] = None
    arguments: Optional[Tuple[Expression, ...]] = None

    def __init__(self, generator, arguments):
        self.generator = generator
        self.arguments = arguments

    def __eq__(self, other):
        if not isinstance(other, Gate):
            return False
        return _compare_gate_classes(self, other)

    @property
    def name(self) -> Optional[str]:
        return self.generator.__name__ if self.generator else "<anonymous>"

    @property
    def is_anonymous(self) -> bool:
        return self.arguments is None

    @abstractmethod
    def get_qubit_operands(self) -> List[Qubit]:
        """Get the qubit operands of the Gate.

        Returns:
            List of qubits on which the Gate operates.
        """

    @abstractmethod
    def is_identity(self) -> bool:
        """Check wether the Gate is an identity Gate.

        Returns:
            Boolean value stating wether the Gate is an identity Gate.
        """

    @abstractmethod
    def relabel(self, mapping: Mapping[int, int]) -> None:
        """Relabel the qubits using the given mapping.

        Args:
            mapping: Mapping from the indices of the original qubits to the indices of the qubits
            after replacement.
        """


class BlochSphereRotation(Gate):
    generator: Optional[Callable[..., "BlochSphereRotation"]] = None

    def __init__(
        self,
        qubit: Qubit,
        axis: Tuple[float, float, float],
        angle: float,
        phase: float = 0,
        generator=None,
        arguments=None,
    ):
        Gate.__init__(self, generator, arguments)
        self.qubit: Qubit = qubit
        self.axis = normalize_axis(np.array(axis).astype(np.float64))
        self.angle = normalize_angle(angle)
        self.phase = normalize_angle(phase)

    @staticmethod
    def identity(q: Qubit) -> "BlochSphereRotation":
        return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=0, phase=0)

    def __repr__(self):
        return f"BlochSphereRotation({self.qubit}, axis={self.axis}, angle={self.angle}, phase={self.phase})"

    def __eq__(self, other):
        if not isinstance(other, BlochSphereRotation):
            return False

        if self.qubit != other.qubit:
            return False

        if abs(self.phase - other.phase) > ATOL:
            return False

        if np.allclose(self.axis, other.axis):
            return abs(self.angle - other.angle) < ATOL
        if np.allclose(self.axis, -other.axis):
            return abs(self.angle + other.angle) < ATOL
        return False

    def accept(self, visitor: SquirrelIRVisitor):
        visitor.visit_gate(self)
        return visitor.visit_bloch_sphere_rotation(self)

    def get_qubit_operands(self) -> List[Qubit]:
        return [self.qubit]

    def is_identity(self) -> bool:
        # Angle and phase are already normalized.
        return abs(self.angle) < ATOL and abs(self.phase) < ATOL

    def relabel(self, mapping: Mapping[int, int]) -> None:
        """Relabel the qubits using the given mapping.

        Args:
            mapping: Mapping from the indices of the original qubits to the indices of the qubits
            after replacement.
        """
        self.qubit = Qubit(mapping[self.qubit.index])


class MatrixGate(Gate):
    generator: Optional[Callable[..., "MatrixGate"]] = None

    def __init__(self, matrix: np.ndarray, operands: List[Qubit], generator=None, arguments=None):
        Gate.__init__(self, generator, arguments)
        assert len(operands) >= 2, "For 1q gates, please use BlochSphereRotation"
        assert matrix.shape == (1 << len(operands), 1 << len(operands))

        self.matrix = matrix
        self.operands = operands

    def __repr__(self):
        return f"MatrixGate(qubits={self.operands}, matrix={self.matrix})"

    def accept(self, visitor: SquirrelIRVisitor):
        visitor.visit_gate(self)
        return visitor.visit_matrix_gate(self)

    def get_qubit_operands(self) -> List[Qubit]:
        return self.operands

    def is_identity(self) -> bool:
        return np.allclose(self.matrix, np.eye(2 ** len(self.operands)))

    def relabel(self, mapping: Mapping[int, int]) -> None:
        """Relabel the qubits using the given mapping.

        Args:
            mapping: Mapping from the indices of the original qubits to the indices of the qubits
            after replacement.
        """
        self.operands = [Qubit(mapping[qubit.index]) for qubit in self.operands]


class ControlledGate(Gate):
    generator: Optional[Callable[..., "ControlledGate"]] = None

    def __init__(self, control_qubit: Qubit, target_gate: Gate, generator=None, arguments=None):
        Gate.__init__(self, generator, arguments)
        self.control_qubit = control_qubit
        self.target_gate = target_gate

    def __repr__(self):
        return f"ControlledGate(control_qubit={self.control_qubit}, {self.target_gate})"

    def accept(self, visitor: SquirrelIRVisitor):
        visitor.visit_gate(self)
        return visitor.visit_controlled_gate(self)

    def get_qubit_operands(self) -> List[Qubit]:
        return [self.control_qubit] + self.target_gate.get_qubit_operands()

    def is_identity(self) -> bool:
        return self.target_gate.is_identity()

    def relabel(self, mapping: Mapping[int, int]) -> None:
        """Relabel the qubits using the given mapping.

        Args:
            mapping: Mapping from the indices of the original qubits to the indices of the qubits
            after replacement.
        """
        self.control_qubit = Qubit(mapping[self.control_qubit.index])
        self.target_gate.relabel(mapping)


def _compare_gate_classes(g1: Gate, g2: Gate) -> bool:
    union_mapping = list(set(g1.get_qubit_operands()) | set(g2.get_qubit_operands()))

    from opensquirrel.utils.matrix_expander import get_matrix_after_qubit_remapping

    matrix_g1 = get_matrix_after_qubit_remapping([g1], union_mapping)
    matrix_g2 = get_matrix_after_qubit_remapping([g2], union_mapping)

    return are_matrices_equivalent_up_to_global_phase(matrix_g1, matrix_g2)


def named_gate(gate_generator: Callable[..., Gate]) -> Callable[..., Gate]:
    @wraps(gate_generator)
    def wrapper(*args, **kwargs):
        result = gate_generator(*args, **kwargs)
        result.generator = wrapper

        all_args = []
        arg_index = 0
        for par in inspect.signature(gate_generator).parameters.values():
            if not issubclass(par.annotation, Expression):
                raise TypeError("Gate argument types must be expressions")

            if par.name in kwargs:
                all_args.append(kwargs[par.name])
            else:
                all_args.append(args[arg_index])
                arg_index += 1

        result.arguments = tuple(all_args)
        return result

    return wrapper


def named_measurement(measurement_generator: Callable[..., Measure]) -> Callable[..., Measure]:
    @wraps(measurement_generator)
    def wrapper(*args, **kwargs):
        result = measurement_generator(*args, **kwargs)
        result.generator = wrapper

        all_args = []
        arg_index = 0
        for par in inspect.signature(measurement_generator).parameters.values():
            if not issubclass(par.annotation, Expression):
                raise TypeError("Measurement argument types must be expressions")

            if par.name in kwargs:
                all_args.append(kwargs[par.name])
            else:
                all_args.append(args[arg_index])
                arg_index += 1

        result.arguments = tuple(all_args)
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
    def __init__(self):
        self.statements: List[Statement] = []

    def add_gate(self, gate: Gate):
        self.statements.append(gate)

    def add_measurement(self, measurement: Measure):
        self.statements.append(measurement)

    def add_comment(self, comment: Comment):
        self.statements.append(comment)

    def __eq__(self, other):
        return self.statements == other.statements

    def __repr__(self):
        return f"""IR: {self.statements}"""

    def accept(self, visitor: SquirrelIRVisitor):
        for statement in self.statements:
            statement.accept(visitor)
