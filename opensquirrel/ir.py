from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from functools import wraps
from typing import Any, SupportsFloat, SupportsInt, Union, cast, overload

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray

from opensquirrel.common import (
    ATOL,
    are_matrices_equivalent_up_to_global_phase,
    normalize_angle,
)

REPR_DECIMALS = 5


def repr_round(
    value: float | Axis | NDArray[np.complex64 | np.complex128],
    decimals: int = REPR_DECIMALS,
) -> float | NDArray[np.complex64 | np.complex128]:
    return np.round(value, decimals)


class IRVisitor:
    def visit_comment(self, comment: Comment) -> Any:
        pass

    def visit_int(self, i: Int) -> Any:
        pass

    def visit_float(self, f: Float) -> Any:
        pass

    def visit_bit(self, qubit: Bit) -> Any:
        pass

    def visit_qubit(self, qubit: Qubit) -> Any:
        pass

    def visit_gate(self, gate: Gate) -> Any:
        pass

    def visit_axis(self, axis: Axis) -> Any:
        pass

    def visit_measure(self, measure: Measure) -> Any:
        pass

    def visit_reset(self, reset: Reset) -> Any:
        pass

    def visit_bloch_sphere_rotation(self, bloch_sphere_rotation: BlochSphereRotation) -> Any:
        pass

    def visit_matrix_gate(self, matrix_gate: MatrixGate) -> Any:
        pass

    def visit_controlled_gate(self, controlled_gate: ControlledGate) -> Any:
        pass

    def visit_directive(self, directive: Directive) -> Any:
        pass

    def visit_barrier_gate(self, barrier: Barrier) -> Any:
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

    def __post_init__(self) -> None:
        if isinstance(self.value, SupportsFloat):
            self.value = float(self.value)
        else:
            msg = "value must be a float"
            raise TypeError(msg)


@dataclass(init=False)
class Int(Expression):
    """Integers used for intermediate representation of ``Statement`` arguments.

    Attributes:
        value: value of the ``Int`` object.
    """

    value: int

    def __init__(self, value: SupportsInt) -> None:
        """Init of the ``Int`` object.

        Args:
            value: value of the ``Int`` object.
        """
        if isinstance(value, SupportsInt):
            self.value = int(value)
            return

        msg = "value must be an int"
        raise TypeError(msg)

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_int(self)

    def __int__(self) -> int:
        """Cast the ``Int`` object to a building python ``int``.

        Returns:
            Building python ``int`` representation of the ``Int``.
        """
        return self.value


@dataclass
class Bit(Expression):
    index: int

    def __hash__(self) -> int:
        return hash(str(self.__class__) + str(self.index))

    def __repr__(self) -> str:
        return f"Bit[{self.index}]"

    def __post_init__(self) -> None:
        if isinstance(self.index, SupportsInt):
            self.index = int(self.index)
        else:
            msg = "index must be an int"
            raise TypeError(msg)

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_bit(self)


@dataclass(init=False)
class Qubit(Expression):
    """``Qubit`` is used for intermediate representation of ``Statement`` arguments.

    Attributes:
        index: index of the ``Qubit`` object.
    """

    index: int

    def __init__(self, index: QubitLike) -> None:
        """Init of the ``Qubit`` object.

        Args:
            index: index of the ``Qubit`` object.
        """
        if isinstance(index, SupportsInt):
            self.index = int(index)
        elif isinstance(index, Qubit):
            self.index = index.index
        else:
            msg = "index must be a QubitLike"
            raise TypeError(msg)

    def __hash__(self) -> int:
        """Create a hash for this qubit."""
        return hash(str(self.__class__) + str(self.index))

    def __repr__(self) -> str:
        """String representation of the Qubit."""
        return f"Qubit[{self.index}]"

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_qubit(self)


class Axis(Sequence[np.float64], Expression):
    """The ``Axis`` object parses and stores a vector containing 3 elements.

    The input vector is always normalized before it is stored.
    """

    _len = 3

    def __init__(self, *axis: AxisLike) -> None:
        """Init of the ``Axis`` object.

        axis: An ``AxisLike`` to create the axis from.
        """
        axis_to_parse = axis[0] if len(axis) == 1 else cast(AxisLike, axis)
        self._value = self._parse_and_validate_axislike(axis_to_parse)

    @property
    def value(self) -> NDArray[np.float64]:
        """The ``Axis`` data saved as a 1D-Array with 3 elements."""
        return self._value

    @value.setter
    def value(self, axis: AxisLike) -> None:
        """Parse and set a new axis.

        Args:
            axis: An ``AxisLike`` to create the axis from.
        """
        self._value = self._parse_and_validate_axislike(axis)

    @classmethod
    def _parse_and_validate_axislike(cls, axis: AxisLike) -> NDArray[np.float64]:
        """Parse and validate an ``AxisLike``.

        Check if the `axis` can be cast to a 1DArray of length 3, raise an error
        otherwise. After casting to an array, the axis is normalized.

        Args:
            axis: ``AxisLike`` to validate and parse.

        Returns:
            Parsed axis represented as a 1DArray of length 3.
        """
        if isinstance(axis, Axis):
            return axis.value

        try:
            axis = np.asarray(axis, dtype=float)
        except (ValueError, TypeError) as e:
            msg = "axis requires an ArrayLike"
            raise TypeError(msg) from e
        axis = axis.flatten()
        if len(axis) != 3:
            msg = f"axis requires an ArrayLike of length 3, but received an ArrayLike of length {len(axis)}"
            raise ValueError(msg)
        return cls._normalize_axis(axis)

    @staticmethod
    def _normalize_axis(axis: NDArray[np.float64]) -> NDArray[np.float64]:
        """Normalize a NDArray.

        Args:
            axis: NDArray to normalize.

        Returns:
            Normalized NDArray.
        """
        return axis / np.linalg.norm(axis)

    @overload
    def __getitem__(self, i: int, /) -> np.float64: ...

    @overload
    def __getitem__(self, s: slice, /) -> list[np.float64]: ...

    def __getitem__(self, index: int | slice, /) -> np.float64 | list[np.float64]:
        """Get the item at `index`."""
        return cast(np.float64, self.value[index])

    def __len__(self) -> int:
        """Length of the axis, which is always 3."""
        return self._len

    def __repr__(self) -> str:
        """String representation of the ``Axis``."""
        return f"Axis{self.value}"

    def __array__(self, dtype: DTypeLike = None, *, copy: bool = True) -> NDArray[Any]:
        """Convert the ``Axis`` data to an array."""
        return np.array(self.value, dtype=dtype, copy=copy)

    def accept(self, visitor: IRVisitor) -> Any:
        """Accept the ``Axis``."""
        return visitor.visit_axis(self)

    def __eq__(self, other: Any) -> bool:
        """Check if `self` is equal to other.

        Two ``Axis`` objects are considered equal if their axes are equal.
        """
        if not isinstance(other, Axis):
            return False
        return np.array_equal(self, other)


class Statement(IRNode, ABC):
    pass


class Measure(Statement, ABC):
    def __init__(
        self,
        qubit: QubitLike,
        bit: Bit,
        axis: AxisLike = (0, 0, 1),
        generator: Callable[..., Measure] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ) -> None:
        self.generator = generator
        self.arguments = arguments
        self.qubit = Qubit(qubit)
        self.bit: Bit = bit
        self.axis = Axis(axis)

    def __repr__(self) -> str:
        return f"Measure(qubit={self.qubit}, bit={self.bit}, axis={self.axis})"

    @property
    def name(self) -> str:
        return self.generator.__name__ if self.generator else "<abstract_measure>"

    @property
    def is_abstract(self) -> bool:
        return self.arguments is None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Measure):
            return False
        return self.qubit == other.qubit and np.allclose(self.axis, other.axis, atol=ATOL)

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_measure(self)

    def get_bit_operands(self) -> list[Bit]:
        return [self.bit]

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]


class Reset(Statement, ABC):
    def __init__(
        self,
        qubit: QubitLike,
        generator: Callable[..., Reset] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ) -> None:
        self.generator = generator
        self.arguments = arguments
        self.qubit = Qubit(qubit)

    def __repr__(self) -> str:
        return f"Reset(qubit={self.qubit})"

    @property
    def name(self) -> str:
        return self.generator.__name__ if self.generator else "<abstract_reset>"

    @property
    def is_abstract(self) -> bool:
        return self.arguments is None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Reset):
            return False
        return self.qubit == other.qubit

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_reset(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]


class Directive(Statement, ABC):
    def __init__(
        self,
        generator: Callable[..., Directive] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ) -> None:
        self.generator = generator
        self.arguments = arguments

    @property
    def name(self) -> str:
        if self.generator:
            return self.generator.__name__
        return "Anonymous directive: " + self.__repr__()

    @property
    def is_abstract(self) -> bool:
        return self.arguments is None

    @abstractmethod
    def get_qubit_operands(self) -> list[Qubit]:
        """Get the qubit operands of the Gate.

        Returns:
            List of qubits on which the Gate operates.
        """


class Barrier(Directive):
    def __init__(
        self,
        qubit: QubitLike,
        generator: Callable[..., Barrier] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ) -> None:
        Directive.__init__(self, generator, arguments)
        self.generator = generator
        self.arguments = arguments
        self.qubit = Qubit(qubit)

    def __repr__(self) -> str:
        return f"Barrier(qubit={self.qubit})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Barrier):
            return False

        return self.qubit == other.qubit

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_directive(self)
        return visitor.visit_barrier_gate(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]

    def is_identity(self) -> bool:
        return False


class Gate(Statement, ABC):
    def __init__(
        self,
        generator: Callable[..., Gate] | None = None,
        arguments: tuple[Expression, ...] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        # Note: two gates are considered equal even when their
        # generators/arguments are different.
        self.generator = generator
        self.arguments = arguments

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Gate):
            return False
        return compare_gates(self, other)

    @property
    def name(self) -> str:
        if self.generator:
            return self.generator.__name__
        return "Anonymous gate: " + self.__repr__()

    @property
    def is_anonymous(self) -> bool:
        return self.arguments is None

    @staticmethod
    def _check_repeated_qubit_operands(qubits: Sequence[Qubit]) -> bool:
        """Check if qubit operands are repeated.

        Args:
            qubits: Sequence of qubits.

        Returns:
            Whether qubit operands are repeated.
        """
        return len(qubits) != len(set(qubits))

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
        qubit: QubitLike,
        axis: AxisLike,
        angle: float,
        phase: float = 0,
        generator: Callable[..., BlochSphereRotation] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ) -> None:
        Gate.__init__(self, generator, arguments)
        self.qubit = Qubit(qubit)
        self.axis = Axis(axis)
        self.angle = normalize_angle(angle)
        self.phase = normalize_angle(phase)

    @staticmethod
    def identity(q: QubitLike) -> BlochSphereRotation:
        return BlochSphereRotation(qubit=q, axis=(1, 0, 0), angle=0, phase=0)

    def __repr__(self) -> str:
        return (
            f"BlochSphereRotation({self.qubit}, axis={repr_round(self.axis)}, angle={repr_round(self.angle)},"
            f" phase={repr_round(self.phase)})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlochSphereRotation):
            return False

        if self.qubit != other.qubit:
            return False

        if abs(self.phase - other.phase) > ATOL:
            return False

        if np.allclose(self.axis, other.axis):
            return abs(self.angle - other.angle) < ATOL
        if np.allclose(self.axis, -other.axis.value):
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
        matrix: ArrayLike | list[list[int | DTypeLike]],
        operands: Iterable[QubitLike],
        generator: Callable[..., MatrixGate] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ) -> None:
        Gate.__init__(self, generator, arguments)

        qubit_operands = [Qubit(operand) for operand in operands]
        if len(qubit_operands) < 2:
            msg = "for 1q gates, please use BlochSphereRotation"
            raise ValueError(msg)

        if self._check_repeated_qubit_operands(qubit_operands):
            msg = "control and target qubit cannot be the same"
            raise ValueError(msg)

        matrix = np.asarray(matrix, dtype=np.complex128)

        if matrix.shape != (1 << len(qubit_operands), 1 << len(qubit_operands)):
            msg = (
                f"incorrect matrix shape. "
                f"Expected {(1 << len(qubit_operands), 1 << len(qubit_operands))} but received {matrix.shape}"
            )
            raise ValueError(msg)

        self.matrix = matrix
        self.operands = qubit_operands

    def __repr__(self) -> str:
        return f"MatrixGate(qubits={self.operands}, matrix={repr_round(self.matrix)})"

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
        control_qubit: QubitLike,
        target_gate: Gate,
        generator: Callable[..., ControlledGate] | None = None,
        arguments: tuple[Expression, ...] | None = None,
    ) -> None:
        Gate.__init__(self, generator, arguments)
        self.control_qubit = Qubit(control_qubit)
        self.target_gate = target_gate

        if self._check_repeated_qubit_operands([self.control_qubit, *target_gate.get_qubit_operands()]):
            msg = "control and target qubit cannot be the same"
            raise ValueError(msg)

    def __repr__(self) -> str:
        return f"ControlledGate(control_qubit={self.control_qubit}, {self.target_gate})"

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_gate(self)
        return visitor.visit_controlled_gate(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.control_qubit, *self.target_gate.get_qubit_operands()]

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

        all_args: list[Expression] = []
        for par in inspect.signature(gate_generator).parameters.values():
            next_arg = kwargs[par.name] if par.name in kwargs else args[len(all_args)]
            next_annotation = (
                ANNOTATIONS_TO_TYPE_MAP[par.annotation] if isinstance(par.annotation, str) else par.annotation
            )

            # Convert to correct expression for IR
            if is_int_annotation(next_annotation):
                next_arg = Int(next_arg)
            if is_qubit_like_annotation(next_annotation):
                next_arg = Qubit(next_arg)

            # Append parsed argument
            all_args.append(next_arg)

        result.arguments = tuple(all_args)
        return result

    return wrapper


def named_measure(measure_generator: Callable[..., Measure]) -> Callable[..., Measure]:
    @wraps(measure_generator)
    def wrapper(*args: Any, **kwargs: Any) -> Measure:
        result = measure_generator(*args, **kwargs)
        result.generator = wrapper

        all_args: list[Any] = []
        for par in inspect.signature(measure_generator).parameters.values():
            next_arg = kwargs[par.name] if par.name in kwargs else args[len(all_args)]
            next_annotation = (
                ANNOTATIONS_TO_TYPE_MAP[par.annotation] if isinstance(par.annotation, str) else par.annotation
            )

            # Convert to correct expression for IR
            if is_qubit_like_annotation(next_annotation):
                next_arg = Qubit(next_arg)

            # Append parsed argument
            all_args.append(next_arg)

        result.arguments = tuple(all_args)
        return result

    return wrapper


def named_reset(reset_generator: Callable[..., Reset]) -> Callable[..., Reset]:
    @wraps(reset_generator)
    def wrapper(*args: Any, **kwargs: Any) -> Reset:
        result = reset_generator(*args, **kwargs)
        result.generator = wrapper

        all_args: list[Any] = []
        for par in inspect.signature(reset_generator).parameters.values():
            next_arg = kwargs[par.name] if par.name in kwargs else args[len(all_args)]
            next_annotation = (
                ANNOTATIONS_TO_TYPE_MAP[par.annotation] if isinstance(par.annotation, str) else par.annotation
            )

            # Convert to correct expression for IR
            if is_qubit_like_annotation(next_annotation):
                next_arg = Qubit(next_arg)

            # Append parsed argument
            all_args.append(next_arg)

        result.arguments = tuple(all_args)
        return result

    return wrapper


def named_directive(directive_generator: Callable[..., Directive]) -> Callable[..., Directive]:
    @wraps(directive_generator)
    def wrapper(*args: Any, **kwargs: Any) -> Directive:
        result = directive_generator(*args, **kwargs)
        result.generator = wrapper

        all_args: list[Any] = []
        for par in inspect.signature(directive_generator).parameters.values():
            next_arg = kwargs[par.name] if par.name in kwargs else args[len(all_args)]
            next_annotation = (
                ANNOTATIONS_TO_TYPE_MAP[par.annotation] if isinstance(par.annotation, str) else par.annotation
            )

            # Convert to correct expression for IR
            if is_qubit_like_annotation(next_annotation):
                next_arg = Qubit(next_arg)

            # Append parsed argument
            all_args.append(next_arg)

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
        if "*/" in self.str:
            msg = "comment contains illegal characters"
            raise ValueError(msg)

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_comment(self)


class IR:
    # This is just a list of gates (for now?)
    def __init__(self) -> None:
        self.statements: list[Statement] = []

    def add_gate(self, gate: Gate) -> None:
        self.statements.append(gate)

    def add_measure(self, measure: Measure) -> None:
        self.statements.append(measure)

    def add_reset(self, reset: Reset) -> None:
        self.statements.append(reset)

    def add_comment(self, comment: Comment) -> None:
        self.statements.append(comment)

    def add_directive(self, directive: Directive) -> None:
        self.statements.append(directive)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, IR):
            return False

        return self.statements == other.statements

    def __repr__(self) -> str:
        return f"IR: {self.statements}"

    def accept(self, visitor: IRVisitor) -> None:
        for statement in self.statements:
            statement.accept(visitor)


# Type Aliases
AxisLike = Union[ArrayLike, Axis]
QubitLike = Union[SupportsInt, Qubit]


def is_qubit_like_annotation(annotation: Any) -> bool:
    return annotation in (QubitLike, Qubit)


def is_int_annotation(annotation: Any) -> bool:
    return annotation in (SupportsInt, Int)


ANNOTATIONS_TO_TYPE_MAP = {
    "AxisLike": AxisLike,
    "BlochSphereRotation": BlochSphereRotation,
    "ControlledGate": ControlledGate,
    "Float": Float,
    "MatrixGate": MatrixGate,
    "SupportsInt": SupportsInt,
    "Qubit": Qubit,
    "QubitLike": QubitLike,
}
