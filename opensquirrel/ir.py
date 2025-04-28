from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, SupportsFloat, SupportsInt, Union, cast, overload, runtime_checkable

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray

from opensquirrel.common import ATOL, are_matrices_equivalent_up_to_global_phase, normalize_angle

REPR_DECIMALS = 5


def repr_round(value: float | Axis | NDArray[np.complex128], decimals: int = REPR_DECIMALS) -> str:
    """
    Given a numerical value (of type `float`, `Axis`, or `NDArray[np.complex128]`):
    - rounds it to `REPR_DECIMALS`,
    - converts it to string, and
    - removes the newlines.

    Returns:
        A single-line string representation of a numerical value.
    """
    return f"{np.round(value, decimals)}".replace("\n", "")


class IRVisitor:
    def visit_str(self, s: String) -> Any:
        pass

    def visit_int(self, i: Int) -> Any:
        pass

    def visit_float(self, f: Float) -> Any:
        pass

    def visit_bit(self, bit: Bit) -> Any:
        pass

    def visit_qubit(self, qubit: Qubit) -> Any:
        pass

    def visit_axis(self, axis: Axis) -> Any:
        pass

    def visit_statement(self, statement: Statement) -> Any:
        pass

    def visit_asm_declaration(self, asm_declaration: AsmDeclaration) -> Any:
        pass

    def visit_instruction(self, instruction: Instruction) -> Any:
        pass

    def visit_unitary(self, unitary: Unitary) -> Any:
        pass

    def visit_gate(self, gate: Gate) -> Any:
        pass

    def visit_bloch_sphere_rotation(self, bloch_sphere_rotation: BlochSphereRotation) -> Any:
        pass

    def visit_bsr_no_params(self, gate: BsrNoParams) -> Any:
        pass

    def visit_bsr_full_params(self, gate: BsrFullParams) -> Any:
        pass

    def visit_bsr_angle_param(self, gate: BsrAngleParam) -> Any:
        pass

    def visit_matrix_gate(self, matrix_gate: MatrixGate) -> Any:
        pass

    def visit_swap(self, gate: SWAP) -> Any:
        pass

    def visit_controlled_gate(self, gate: ControlledGate) -> Any:
        pass

    def visit_cnot(self, gate: CNOT) -> Any:
        pass

    def visit_cz(self, gate: CZ) -> Any:
        pass

    def visit_cr(self, gate: CR) -> Any:
        pass

    def visit_crk(self, gate: CRk) -> Any:
        pass

    def visit_non_unitary(self, gate: NonUnitary) -> Any:
        pass

    def visit_measure(self, measure: Measure) -> Any:
        pass

    def visit_init(self, init: Init) -> Any:
        pass

    def visit_reset(self, reset: Reset) -> Any:
        pass

    def visit_barrier(self, barrier: Barrier) -> Any:
        pass

    def visit_wait(self, wait: Wait) -> Any:
        pass


class IRNode(ABC):
    @abstractmethod
    def accept(self, visitor: IRVisitor) -> Any:
        pass


class Expression(IRNode, ABC):
    pass


@runtime_checkable
class SupportsStr(Protocol):
    def __str__(self) -> str: ...


@dataclass(init=False)
class String(Expression):
    """Strings used for intermediate representation of ``Statement`` arguments.

    Attributes:
        value: value of the ``String`` object.
    """

    value: str

    def __init__(self, value: SupportsStr) -> None:
        """Init of the ``String`` object.

        Args:
            value: value of the ``String`` object.
        """
        if isinstance(value, SupportsStr):
            self.value = str(value)
            return

        msg = "value must be a str"
        raise TypeError(msg)

    def __str__(self) -> str:
        """Cast the ``String`` object to a built-in Python ``str``.

        Returns:
            Built-in Python ``str`` representation of the ``String``.
        """
        return self.value

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_str(self)


@dataclass(init=False)
class Float(Expression):
    """Floats used for intermediate representation of ``Statement`` arguments.

    Attributes:
        value: value of the ``Float`` object.
    """

    value: float

    def __init__(self, value: SupportsFloat) -> None:
        """Init of the ``Float`` object.

        Args:
            value: value of the ``Float`` object.
        """
        if isinstance(value, SupportsFloat):
            self.value = float(value)
            return

        msg = "value must be a float"
        raise TypeError(msg)

    def __float__(self) -> float:
        """Cast the ``Float`` object to a built-in Python ``float``.

        Returns:
            Built-in Python ``float`` representation of the ``Float``.
        """
        return self.value

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_float(self)


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

    def __int__(self) -> int:
        """Cast the ``Int`` object to a built-in Python ``int``.

        Returns:
            Built-in Python ``int`` representation of the ``Int``.
        """
        return self.value

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_int(self)


@dataclass(init=False)
class Bit(Expression):
    index: int

    def __init__(self, index: BitLike) -> None:
        if isinstance(index, SupportsInt):
            self.index = int(index)
        elif isinstance(index, Bit):
            self.index = index.index
        else:
            msg = "index must be a BitLike"
            raise TypeError(msg)

    def __hash__(self) -> int:
        return hash(str(self.__class__) + str(self.index))

    def __repr__(self) -> str:
        return f"Bit[{self.index}]"

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
        if isinstance(index, SupportsInt):
            self.index = int(index)
        elif isinstance(index, Qubit):
            self.index = index.index
        else:
            msg = "index must be a QubitLike"
            raise TypeError(msg)

    def __hash__(self) -> int:
        return hash(str(self.__class__) + str(self.index))

    def __repr__(self) -> str:
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
        axis_to_parse = axis[0] if len(axis) == 1 else cast("AxisLike", axis)
        self._value = self.normalize(self.parse(axis_to_parse))

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
        self._value = self.parse(axis)
        self._value = self.normalize(self._value)

    @staticmethod
    def parse(axis: AxisLike) -> NDArray[np.float64]:
        """Parse and validate an ``AxisLike``.

        Check if the `axis` can be cast to a 1DArray of length 3, raise an error otherwise.
        After casting to an array, the axis is normalized.

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
        if np.all(axis == 0):
            msg = "axis requires at least one element to be non-zero"
            raise ValueError(msg)
        return axis

    @staticmethod
    def normalize(axis: NDArray[np.float64]) -> NDArray[np.float64]:
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
        return cast("np.float64", self.value[index])

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
        """Check if `self` is equal to `other`.

        Two ``Axis`` objects are considered equal if their axes are equal.
        """
        if not isinstance(other, Axis):
            return False
        return np.array_equal(self, other)


class Statement(IRNode, ABC):
    pass


class AsmDeclaration(Statement):
    """``AsmDeclaration`` is used to define an assembly declaration statement in the IR.

    Args:
        backend_name: Name of the backend that is to process the provided backend code.
        backend_code: (Assembly) code to be processed by the specified backend.
    """

    def __init__(
        self,
        backend_name: SupportsStr,
        backend_code: SupportsStr,
    ) -> None:
        self.backend_name = String(backend_name)
        self.backend_code = String(backend_code)
        Statement.__init__(self)

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_statement(self)
        return visitor.visit_asm_declaration(self)


class Instruction(Statement, ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @property
    @abstractmethod
    def arguments(self) -> tuple[Expression, ...]:
        pass

    @abstractmethod
    def get_qubit_operands(self) -> list[Qubit]:
        pass

    @abstractmethod
    def get_bit_operands(self) -> list[Bit]:
        pass


class Unitary(Instruction, ABC):
    def __init__(self, name: str) -> None:
        Instruction.__init__(self, name)


class Gate(Unitary, ABC):
    def __init__(self, name: str) -> None:
        Unitary.__init__(self, name)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Gate):
            return False
        return compare_gates(self, other)

    @property
    @abstractmethod
    def arguments(self) -> tuple[Expression, ...]:
        pass

    @staticmethod
    def _check_repeated_qubit_operands(qubits: Sequence[Qubit]) -> bool:
        return len(qubits) != len(set(qubits))

    @abstractmethod
    def get_qubit_operands(self) -> list[Qubit]:
        pass

    @abstractmethod
    def get_bit_operands(self) -> list[Bit]:
        pass

    @abstractmethod
    def is_identity(self) -> bool:
        pass


class BlochSphereRotation(Gate):
    def __init__(
        self,
        qubit: QubitLike,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat = 0,
        name: str = "BlochSphereRotation",
    ) -> None:
        Gate.__init__(self, name)
        self.qubit = Qubit(qubit)
        self.axis = Axis(axis)
        self.angle = normalize_angle(angle)
        self.phase = normalize_angle(phase)

    def __repr__(self) -> str:
        return (
            f"{self.name}(qubit={self.qubit}, axis={repr_round(self.axis)}, angle={repr_round(self.angle)}, "
            f"phase={repr_round(self.phase)})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BlochSphereRotation):
            return False

        if self.qubit != other.qubit:
            return False

        if abs(self.phase - other.phase) > ATOL:
            return False

        if np.allclose(self.axis, other.axis, atol=ATOL):
            return abs(self.angle - other.angle) < ATOL
        if np.allclose(self.axis, -other.axis.value, atol=ATOL):
            return abs(self.angle + other.angle) < ATOL
        return False

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return ()

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_bloch_sphere_rotation(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]

    def get_bit_operands(self) -> list[Bit]:
        return []

    def is_identity(self) -> bool:
        # Angle and phase are already normalized.
        return abs(self.angle) < ATOL and abs(self.phase) < ATOL

    @staticmethod
    def try_match_replace_with_default(bsr: BlochSphereRotation) -> BlochSphereRotation:
        """Try replacing a given BlochSphereRotation with a default BlochSphereRotation.
         It does that by matching the input BlochSphereRotation to a default BlochSphereRotation.

        Returns:
             A default BlockSphereRotation if this BlochSphereRotation is close to it,
             or the input BlochSphereRotation otherwise.
        """
        from opensquirrel.default_instructions import (
            default_bsr_with_angle_param_set,
            default_bsr_without_params_set,
        )

        bsr_set_without_rn = {**default_bsr_without_params_set, **default_bsr_with_angle_param_set}
        for gate_name in bsr_set_without_rn:
            arguments: tuple[Any, ...] = (bsr.qubit,)
            if gate_name in default_bsr_with_angle_param_set:
                arguments += (Float(bsr.angle),)
            gate = bsr_set_without_rn[gate_name](*arguments)
            if (
                np.allclose(gate.axis, bsr.axis, atol=ATOL)
                and np.allclose(gate.angle, bsr.angle, atol=ATOL)
                and np.allclose(gate.phase, bsr.phase, atol=ATOL)
            ):
                return gate
        nx, ny, nz = (Float(component) for component in bsr.axis)
        return Rn(bsr.qubit, nx, ny, nz, Float(bsr.angle), Float(bsr.phase))


class BsrNoParams(BlochSphereRotation):
    def __init__(
        self,
        qubit: QubitLike,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat = 0,
        name: str = "BsrNoParams",
    ) -> None:
        BlochSphereRotation.__init__(self, qubit, axis, angle, phase, name)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_bsr_no_params(self)


class I(BsrNoParams):  # noqa: E742
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(1, 0, 0), angle=0, phase=0, name="I")


class H(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(1, 0, 1), angle=math.pi, phase=math.pi / 2, name="H")


class X(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(1, 0, 0), angle=math.pi, phase=math.pi / 2, name="X")


class X90(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(1, 0, 0), angle=math.pi / 2, phase=0, name="X90")


class MinusX90(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(1, 0, 0), angle=-math.pi / 2, phase=-0, name="mX90")


class Y(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 1, 0), angle=math.pi, phase=math.pi / 2, name="Y")


class Y90(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 1, 0), angle=math.pi / 2, phase=0, name="Y90")


class MinusY90(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 1, 0), angle=-math.pi / 2, phase=0, name="mY90")


class Z(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=math.pi, phase=math.pi / 2, name="Z")


class S(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=math.pi / 2, phase=0, name="S")


class SDagger(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=-math.pi / 2, phase=0, name="Sdag")


class T(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=math.pi / 4, phase=0, name="T")


class TDagger(BsrNoParams):
    def __init__(self, qubit: QubitLike) -> None:
        BsrNoParams.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=-math.pi / 4, phase=0, name="Tdag")


class BsrFullParams(BlochSphereRotation):
    def __init__(
        self,
        qubit: QubitLike,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat,
        name: str = "BsrFullParams",
    ) -> None:
        BlochSphereRotation.__init__(self, qubit, axis, angle, phase, name)
        self.nx, self.ny, self.nz = (Float(component) for component in Axis(axis))
        self.theta = Float(angle)
        self.phi = Float(phase)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.qubit, self.nx, self.ny, self.nz, self.theta, self.phi

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_bsr_full_params(self)


class Rn(BsrFullParams):
    def __init__(
        self,
        qubit: QubitLike,
        nx: SupportsFloat,
        ny: SupportsFloat,
        nz: SupportsFloat,
        theta: SupportsFloat,
        phi: SupportsFloat,
    ) -> None:
        axis: AxisLike = Axis(np.asarray([nx, ny, nz], dtype=np.float64))
        BsrFullParams.__init__(self, qubit=qubit, axis=axis, angle=theta, phase=phi, name="Rn")


class BsrAngleParam(BlochSphereRotation):
    def __init__(
        self,
        qubit: QubitLike,
        axis: AxisLike,
        angle: SupportsFloat,
        phase: SupportsFloat = 0,
        name: str = "BsrNoParams",
    ) -> None:
        BlochSphereRotation.__init__(self, qubit, axis, angle, phase, name)
        self.theta = Float(angle)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.qubit, self.theta

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_bsr_angle_param(self)


class Rx(BsrAngleParam):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        BsrAngleParam.__init__(self, qubit=qubit, axis=(1, 0, 0), angle=theta, phase=0, name="Rx")


class Ry(BsrAngleParam):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        BsrAngleParam.__init__(self, qubit=qubit, axis=(0, 1, 0), angle=theta, phase=0, name="Ry")


class Rz(BsrAngleParam):
    def __init__(self, qubit: QubitLike, theta: SupportsFloat) -> None:
        BsrAngleParam.__init__(self, qubit=qubit, axis=(0, 0, 1), angle=theta, phase=0, name="Rz")


class MatrixGate(Gate):
    def __init__(
        self, matrix: ArrayLike | list[list[int | DTypeLike]], operands: Iterable[QubitLike], name: str = "MatrixGate"
    ) -> None:
        Gate.__init__(self, name)
        qubit_operands = [Qubit(operand) for operand in operands]
        if len(qubit_operands) < 2:
            msg = "for 1q gates, please use BlochSphereRotation"
            raise ValueError(msg)

        if self._check_repeated_qubit_operands(qubit_operands):
            msg = "operands cannot be the same"
            raise ValueError(msg)

        matrix = np.asarray(matrix, dtype=np.complex128)

        expected_number_of_rows = 1 << len(qubit_operands)
        expected_number_of_cols = expected_number_of_rows
        if matrix.shape != (expected_number_of_rows, expected_number_of_cols):
            msg = (
                f"incorrect matrix shape. "
                f"Expected {(expected_number_of_rows, expected_number_of_cols)} but received {matrix.shape}"
            )
            raise ValueError(msg)

        self.matrix = matrix
        self.operands = qubit_operands

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return ()

    def __repr__(self) -> str:
        return f"{self.name}(qubits={self.operands}, matrix={repr_round(self.matrix)})"

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_matrix_gate(self)

    def get_qubit_operands(self) -> list[Qubit]:
        return self.operands

    def get_bit_operands(self) -> list[Bit]:
        return []

    def is_identity(self) -> bool:
        return np.allclose(self.matrix, np.eye(2 ** len(self.operands)), atol=ATOL)


class SWAP(MatrixGate):
    def __init__(self, qubit_0: QubitLike, qubit_1: QubitLike) -> None:
        MatrixGate.__init__(
            self,
            matrix=np.array(
                [
                    [1, 0, 0, 0],
                    [0, 0, 1, 0],
                    [0, 1, 0, 0],
                    [0, 0, 0, 1],
                ],
            ),
            operands=[qubit_0, qubit_1],
            name="SWAP",
        )
        self.qubit_0 = Qubit(qubit_0)
        self.qubit_1 = Qubit(qubit_1)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.qubit_0, self.qubit_1

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_swap(self)


class ControlledGate(Gate):
    def __init__(self, control_qubit: QubitLike, target_gate: Gate, name: str = "ControlledGate") -> None:
        Gate.__init__(self, name)
        self.control_qubit = Qubit(control_qubit)
        self.target_gate = target_gate

        if self._check_repeated_qubit_operands([self.control_qubit, *target_gate.get_qubit_operands()]):
            msg = "control and target qubit cannot be the same"
            raise ValueError(msg)

    def __repr__(self) -> str:
        return f"{self.name}(control_qubit={self.control_qubit}, target_gate={self.target_gate})"

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_controlled_gate(self)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return ()

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.control_qubit, *self.target_gate.get_qubit_operands()]

    def get_bit_operands(self) -> list[Bit]:
        return []

    def is_identity(self) -> bool:
        return self.target_gate.is_identity()


class CNOT(ControlledGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike) -> None:
        ControlledGate.__init__(self, control_qubit=control_qubit, target_gate=X(target_qubit), name="CNOT")
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.control_qubit, self.target_qubit

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_cnot(self)


class CZ(ControlledGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike) -> None:
        ControlledGate.__init__(self, control_qubit=control_qubit, target_gate=Z(target_qubit), name="CZ")
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.control_qubit, self.target_qubit

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_cz(self)


class CR(ControlledGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike, theta: SupportsFloat) -> None:
        ControlledGate.__init__(
            self,
            control_qubit=control_qubit,
            target_gate=BlochSphereRotation(qubit=target_qubit, axis=(0, 0, 1), angle=theta, phase=float(theta) / 2),
            name="CR",
        )
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)
        self.theta = Float(theta)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.control_qubit, self.target_qubit, self.theta

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_cr(self)


class CRk(ControlledGate):
    def __init__(self, control_qubit: QubitLike, target_qubit: QubitLike, k: SupportsInt) -> None:
        theta = 2 * math.pi / (2 ** int(k))
        ControlledGate.__init__(
            self,
            control_qubit=control_qubit,
            target_gate=BlochSphereRotation(qubit=target_qubit, axis=(0, 0, 1), angle=theta, phase=float(theta) / 2),
            name="CRk",
        )
        self.control_qubit = Qubit(control_qubit)
        self.target_qubit = Qubit(target_qubit)
        self.k = Int(k)

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.control_qubit, self.target_qubit, self.k

    def accept(self, visitor: IRVisitor) -> Any:
        return visitor.visit_crk(self)


class NonUnitary(Instruction, ABC):
    def __init__(self, qubit: QubitLike, name: str) -> None:
        Instruction.__init__(self, name)
        self.qubit = Qubit(qubit)

    @property
    @abstractmethod
    def arguments(self) -> tuple[Expression, ...]:
        pass

    def get_qubit_operands(self) -> list[Qubit]:
        return [self.qubit]

    def get_bit_operands(self) -> list[Bit]:
        return []


class Measure(NonUnitary):
    def __init__(self, qubit: QubitLike, bit: BitLike, axis: AxisLike = (0, 0, 1)) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="measure")
        self.qubit = Qubit(qubit)
        self.bit = Bit(bit)
        self.axis = Axis(axis)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(qubit={self.qubit}, bit={self.bit}, axis={self.axis})"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Measure) and self.qubit == other.qubit and np.allclose(self.axis, other.axis, atol=ATOL)
        )

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.qubit, self.bit

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_non_unitary(self)
        return visitor.visit_measure(self)

    def get_bit_operands(self) -> list[Bit]:
        return [self.bit]


class Init(NonUnitary):
    def __init__(self, qubit: QubitLike) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="init")
        self.qubit = Qubit(qubit)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(qubit={self.qubit})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Init) and self.qubit == other.qubit

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_non_unitary(self)
        return visitor.visit_init(self)


class Reset(NonUnitary):
    def __init__(self, qubit: QubitLike) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="reset")
        self.qubit = Qubit(qubit)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(qubit={self.qubit})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Reset) and self.qubit == other.qubit

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_non_unitary(self)
        return visitor.visit_reset(self)


class Barrier(NonUnitary):
    def __init__(self, qubit: QubitLike) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="barrier")
        self.qubit = Qubit(qubit)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(qubit={self.qubit})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Barrier) and self.qubit == other.qubit

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return (self.qubit,)

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_non_unitary(self)
        return visitor.visit_barrier(self)


class Wait(NonUnitary):
    def __init__(self, qubit: QubitLike, time: SupportsInt) -> None:
        NonUnitary.__init__(self, qubit=qubit, name="wait")
        self.qubit = Qubit(qubit)
        self.time = Int(time)

    def __repr__(self) -> str:
        return f"{self.name}(qubit={self.qubit}, time={self.time})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Wait) and self.qubit == other.qubit and self.time == other.time

    @property
    def arguments(self) -> tuple[Expression, ...]:
        return self.qubit, self.time

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_non_unitary(self)
        return visitor.visit_wait(self)


def compare_gates(g1: Gate, g2: Gate) -> bool:
    union_mapping = [q.index for q in list(set(g1.get_qubit_operands()) | set(g2.get_qubit_operands()))]

    from opensquirrel.circuit_matrix_calculator import get_circuit_matrix
    from opensquirrel.reindexer import get_reindexed_circuit

    matrix_g1 = get_circuit_matrix(get_reindexed_circuit([g1], union_mapping))
    matrix_g2 = get_circuit_matrix(get_reindexed_circuit([g2], union_mapping))

    return are_matrices_equivalent_up_to_global_phase(matrix_g1, matrix_g2)


class IR:
    def __init__(self) -> None:
        self.statements: list[Statement] = []

    def add_asm_declaration(self, asm_declaration: AsmDeclaration) -> None:
        self.statements.append(asm_declaration)

    def add_gate(self, gate: Gate) -> None:
        self.statements.append(gate)

    def add_non_unitary(self, non_unitary: NonUnitary) -> None:
        self.statements.append(non_unitary)

    def add_statement(self, statement: Statement) -> None:
        self.statements.append(statement)

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
BitLike = Union[SupportsInt, Bit]
QubitLike = Union[SupportsInt, Qubit]
