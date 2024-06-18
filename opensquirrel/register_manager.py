from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import cqasm.v3x as cqasm


def is_qubit_type(variable: cqasm.semantic.MultiVariable) -> bool:
    return isinstance(variable.typ, cqasm.types.Qubit) or isinstance(variable.typ, cqasm.types.QubitArray)


@dataclass
class QubitRange:
    first: int = 0
    size: int = 0


class RegisterManager:
    """RegisterManager keeps track of a (virtual) qubit register, i.e., an array of consecutive qubits,
    and the mappings between the (logical) qubit variable names, as used in an input cQASM program,
    and the (virtual) qubit register.

    For example, given an input program that defines 'qubit[3] q':
    - variable 'q' is mapped to qubits 0 to 2 in the qubit register, and
    - positions 0 to 2 in the qubit register are mapped to variable 'q'.

    The mapping of qubit variable names to positions in the qubit register is an implementation detail,
    i.e., it is not guaranteed that qubit register indices are assigned to qubit variable names in the order
    these variables are defined in the input program.
    """

    # TODO:
    # In the future, when variables of different types can be defined (e.g. float q)
    # we will have to prevent a variable being called 'q' or 'b'.
    # A possible way to do this is to introduce variable name mangling in the IR
    # (e.g., store 'float q' as 'float _float__q')
    _default_qubit_register_name = "q"

    def __init__(
        self,
        qubit_register_size: int,
        variable_name_to_qubit_range: dict[str, QubitRange] = dict(),
        qubit_index_to_variable_name: dict[int, str] = dict(),
    ) -> None:
        self.qubit_register_size = qubit_register_size
        self.qubit_register_name = self._default_qubit_register_name
        self.variable_name_to_qubit_range = variable_name_to_qubit_range
        self.qubit_index_to_variable_name = qubit_index_to_variable_name

    def __repr__(self) -> str:
        return (
            f"qubit_register_size: {self.qubit_register_size}\n"
            f"variable_name_to_qubit_range: {self.variable_name_to_qubit_range}\n"
            f"qubit_index_to_variable_name: {self.qubit_index_to_variable_name}"
        )

    @staticmethod
    def _parse_ast_string(string: str) -> str:
        # FIXME: libqasm should return bytes, not the __repr__ of a bytes object ("b'q'")
        return string[2:-1]

    @classmethod
    def from_ast(cls, ast: cqasm.semantic.Program) -> RegisterManager:
        qubit_register_size: int = 0
        variable_name_to_qubit_range: dict[str, QubitRange] = dict()
        qubit_index_to_variable_name: dict[int, str] = dict()

        qubit_variables = [v for v in ast.variables if is_qubit_type(v)]
        qubit_register_size = sum([qv.typ.size for qv in qubit_variables])
        current_qubit_index: int = 0
        for qv in qubit_variables:
            qv_name = RegisterManager._parse_ast_string(qv.name)
            qv_size = qv.typ.size
            variable_name_to_qubit_range[qv_name] = QubitRange(current_qubit_index, qv_size)
            for _ in range(qv_size):
                qubit_index_to_variable_name[current_qubit_index] = qv_name
                current_qubit_index += 1
        return cls(qubit_register_size, variable_name_to_qubit_range, qubit_index_to_variable_name)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, RegisterManager):
            return False
        return (
            self.qubit_register_size == other.qubit_register_size
            and self.qubit_register_name == other.qubit_register_name
            and self.variable_name_to_qubit_range == other.variable_name_to_qubit_range
            and self.qubit_index_to_variable_name == other.qubit_index_to_variable_name
        )

    def get_qubit_register_size(self) -> int:
        return self.qubit_register_size

    def get_qubit_range(self, variable_name: str) -> QubitRange:
        return self.variable_name_to_qubit_range[variable_name]

    def get_qubit_indices(self, variable_name: str, indices: Iterable[int]) -> list[int]:
        start_index = self.get_qubit_range(variable_name).first
        return [start_index + i for i in indices]

    def get_variable_name(self, index: int) -> str:
        return self.qubit_register_name[index]
