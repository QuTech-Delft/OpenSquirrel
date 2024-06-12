from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import Any, overload

import numpy as np
from numpy.typing import ArrayLike, NDArray

from opensquirrel.common import ATOL, are_matrices_equivalent_up_to_global_phase, normalize_angle, normalize_axis


class IRVisitor(ABC):
    def visit_comment(self, comment: Comment) -> Any:
        pass

    def visit_int(self, i: Int) -> Any:
        pass

    def visit_float(self, f: Float) -> Any:
        pass

    def visit_qubit(self, qubit: Qubit) -> Any:
        pass

    def visit_gate(self, gate: Gate) -> Any:
        pass

    def visit_measure(self, measure: Measure) -> Any:
        pass

    def visit_bloch_sphere_rotation(self, bloch_sphere_rotation: BlochSphereRotation) -> Any:
        pass

    def visit_matrix_gate(self, matrix_gate: MatrixGate) -> Any:
        pass

    def visit_controlled_gate(self, controlled_gate: ControlledGate) -> Any:
        pass


class IRNode(ABC):
    @abstractmethod
    def accept(self, visitor: IRVisitor) -> Any:
        pass


class Expression(IRNode, ABC):
    pass


@dataclass
class Float(Expression):
    value: float

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_float(self)


@dataclass
class Int(Expression):
    value: int

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_int(self)


@dataclass
class Qubit(Expression):
    index: int

    def __hash__(self) -> int:
        return hash(self.index)

    def __repr__(self) -> str:
        return f"Qubit[{self.index}]"

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_qubit(self)


class Statement(IRNode, ABC):
    pass


class Measure(Statement, ABC):

    def __init__(
        self,
        qubit: Qubit,
        axis: ArrayLike = (0, 0, 1),
        generator: Callable[..., Measure] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ) -> None:
        self.generator = generator
        self.arguments = arguments
        self.qubit: Qubit = qubit
        self.axis = normalize_axis(np.array(axis).astype(np.float64))

    def __repr__(self) -> str:
        return f"Measure({self.qubit}, axis={self.axis})"

    @property
    def name(self) -> str:
        return self.generator.__name__ if self.generator else "<abstract_measurement>"

    @property
    def is_abstract(self) -> bool:
        return self.arguments is None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Measure):
            return False
        return self.qubit == other.qubit and np.allclose(self.axis, other.axis, atol=ATOL)

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_measure(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]


class Gate(Statement, ABC):
    def __init__(
        self,
        generator: Callable[..., Gate] | None = None,
        arguments: tuple[Expression, ...] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # Note: two gates are considered equal even when their generators/arguments are different.
        self.generator = generator
        self.arguments = arguments

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Gate):
            return False
        return compare_gates(self, other)

    @property
    def name(self) -> str:
        return self.generator.__name__ if self.generator else "<anonymous-gate>"

    @property
    def is_anonymous(self) -> bool:
        return self.arguments is None

    @abstractmethod
    def get_qubit_operands(self) -> list[Qubit]:
        """Get the qubit operands of the Gate.

        Returns:
            List of qubits on which the Gate operates.
        """

    @abstractmethod
    def is_identity(self) -> bool:
        """Check whether the Gate is an identity Gate.

        Returns:
            Boolean value stating whether the Gate is an identity Gate.
        """


class BlochSphereRotation(Gate):
    def __init__(
        self,
        qubit: Qubit,
        axis: ArrayLike,
        angle: float,
        phase: float = 0,
        generator: Callable[..., BlochSphereRotation] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ) -> None:
        Gate.__init__(self, generator, arguments)
        self.qubit: Qubit = qubit
        self.axis = normalize_axis(np.array(axis).astype(np.float64))
        self.angle = normalize_angle(angle)
        self.phase = normalize_angle(phase)

    @staticmethod
    def identity(q: Qubit) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=0, phase=0)

    def __repr__(self) -> str:
        return f"BlochSphereRotation({self.qubit}, axis={self.axis}, angle={self.angle}, phase={self.phase})"

    def __eq__(self, other: object) -> bool:
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

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_gate(self)
        return visitor.visit_bloch_sphere_rotation(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]

    def is_identity(self) -> bool:
        # Angle and phase are already normalized.
        return abs(self.angle) < ATOL and abs(self.phase) < ATOL


class MatrixGate(Gate):

    def __init__(
        self,
        matrix: NDArray[np.complex_],
        operands: list[Qubit],
        generator: Callable[..., MatrixGate] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ):
        Gate.__init__(self, generator, arguments)
        assert len(operands) >= 2, "For 1q gates, please use BlochSphereRotation"
        assert matrix.shape == (1 << len(operands), 1 << len(operands))

        self.matrix = matrix
        self.operands = operands

    def __repr__(self) -> str:
        return f"MatrixGate(qubits={self.operands}, matrix={self.matrix})"

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_gate(self)
        return visitor.visit_matrix_gate(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return self.operands

    def is_identity(self) -> bool:
        return np.allclose(self.matrix, np.eye(2 ** len(self.operands)))


class ControlledGate(Gate):

    def __init__(
        self,
        control_qubit: Qubit,
        target_gate: Gate,
        generator: Callable[..., ControlledGate] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ):
        Gate.__init__(self, generator, arguments)
        self.control_qubit = control_qubit
        self.target_gate = target_gate

    def __repr__(self) -> str:
        return f"ControlledGate(control_qubit={self.control_qubit}, {self.target_gate})"

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_gate(self)
        return visitor.visit_controlled_gate(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.control_qubit] + self.target_gate.get_qubit_operands()

    def is_identity(self) -> bool:
        return self.target_gate.is_identity()


@overload
def named_gate(gate_generator: Callable[..., BlochSphereRotation]) -> Callable[..., BlochSphereRotation]: ...


@overload
def named_gate(gate_generator: Callable[..., MatrixGate]) -> Callable[..., MatrixGate]: ...


@overload
def named_gate(gate_generator: Callable[..., ControlledGate]) -> Callable[..., ControlledGate]: ...


def named_gate(gate_generator: Callable[..., Gate]) -> Callable[..., Gate]:
    @wraps(gate_generator)
    def wrapper(*args: Any, **kwargs: Any) -> Gate:
        result = gate_generator(*args, **kwargs)
        result.generator = wrapper

        all_args = []
        arg_index = 0
        for par in inspect.signature(gate_generator).parameters.values():
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
    def wrapper(*args: Any, **kwargs: Any) -> Measure:
        result = measurement_generator(*args, **kwargs)
        result.generator = wrapper

        all_args = []
        arg_index = 0
        for par in inspect.signature(measurement_generator).parameters.values():
            if par.name in kwargs:
                all_args.append(kwargs[par.name])
            else:
                all_args.append(args[arg_index])
                arg_index += 1

        result.arguments = tuple(all_args)
        return result

    return wrapper


def compare_gates(g1: Gate, g2: Gate) -> bool:
    union_mapping = [q.index for q in list(set(g1.get_qubit_operands()) | set(g2.get_qubit_operands()))]

    from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
    from opensquirrel.reindexer import get_reindexed_circuit

    matrix_g1 = get_circuit_matrix(get_reindexed_circuit([g1], union_mapping))
    matrix_g2 = get_circuit_matrix(get_reindexed_circuit([g2], union_mapping))

    return are_matrices_equivalent_up_to_global_phase(matrix_g1, matrix_g2)


@dataclass
class Comment(Statement):
    str: str

    def __post_init__(self) -> None:
        assert "*/" not in self.str, "Comment contains illegal characters"

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_comment(self)


class IR:
    # This is just a list of gates (for now?)
    def __init__(self) -> None:
        self.statements: list[Statement] = []

    def add_gate(self, gate: Gate) -> None:
        self.statements.append(gate)

    def add_measurement(self, measurement: Measure) -> None:
        self.statements.append(measurement)

    def add_comment(self, comment: Comment) -> None:
        self.statements.append(comment)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IR):
            return False

        return self.statements == other.statements

    def __repr__(self) -> str:
        return f"IR: {self.statements}"

    def accept(self, visitor: IRVisitor) -> None:
        for statement in self.statements:
            statement.accept(visitor)
