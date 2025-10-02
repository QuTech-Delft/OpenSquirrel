from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol, SupportsFloat, SupportsInt, Union, cast, overload, runtime_checkable

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray

from opensquirrel.ir.ir import IRNode, IRVisitor


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


class BaseAxis(Sequence[np.float64], Expression, ABC):
    _len = 3

    def __init__(self, *axis: AxisLike) -> None:
        """Init of the ``BaseAxis`` object.

        axis: An ``AxisLike`` to create the axis from.
        """
        self.value = axis[0] if len(axis) == 1 else cast("AxisLike", axis)

    @staticmethod
    @abstractmethod
    def parse(axis: AxisLike) -> NDArray[np.float64]: ...

    @property
    def value(self) -> NDArray[np.float64]:
        """The ``BaseAxis`` data saved as a 1D-Array with 3 elements."""
        return self._value

    @value.setter
    def value(self, axis: AxisLike) -> None:
        """Parse and set a new axis.

        Args:
            axis: An ``AxisLike`` to create the axis from.
        """
        self._value = self.parse(axis)

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
        """String representation of the ``BaseAxis``."""
        return f"{self.__class__.__name__}{self.value}"

    def __array__(self, dtype: DTypeLike = None, *, copy: bool | None = None) -> NDArray[Any]:
        """Convert the ``BaseAxis`` data to an array."""
        return np.array(self.value, dtype=dtype, copy=copy)

    def __eq__(self, other: Any) -> bool:
        """Check if `self` is equal to `other`.

        Two ``BaseAxis`` objects are considered equal if their axes are equal.
        """
        if not isinstance(other, self.__class__):
            return False
        return np.array_equal(self, other)


class Axis(BaseAxis):
    """The ``Axis`` object parses and stores a vector containing 3 elements.

    The input vector is always normalized before it is stored.
    """

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
            axis = np.asarray(axis, dtype=np.float64)
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
        axis = cast("NDArray[np.float64]", axis)
        return axis / np.linalg.norm(axis)

    def accept(self, visitor: IRVisitor) -> Any:
        """Accept the ``Axis``."""
        return visitor.visit_axis(self)


# Type Aliases
BitLike = Union[SupportsInt, Bit]
QubitLike = Union[SupportsInt, Qubit]
AxisLike = Union[ArrayLike, BaseAxis]
