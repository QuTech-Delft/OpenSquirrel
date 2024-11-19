from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING

from opensquirrel.default_instructions import default_gate_set, default_non_unitary_set
from opensquirrel.utils import Singleton

if TYPE_CHECKING:
    from opensquirrel.ir import Gate, NonUnitary


class InstructionLibrary(metaclass=Singleton):
    def __init__(self) -> None:
        self.gate_set = default_gate_set
        self.non_unitary_set = default_non_unitary_set

    def get_gate_set(self) -> Mapping[str, Callable[..., Gate]]:
        return self.gate_set

    def get_non_unitary_set(self) -> Mapping[str, Callable[..., NonUnitary]]:
        return self.non_unitary_set

    def get_gate_f(self, gate_name: str) -> Callable[..., Gate]:
        if gate_name not in self.gate_set:
            msg = f"unknown gate '{gate_name}'"
            raise ValueError(msg)
        return self.gate_set[gate_name]

    def get_non_unitary_f(self, non_unitary_name: str) -> Callable[..., NonUnitary]:
        if non_unitary_name not in self.non_unitary_set:
            msg = f"unknown non-unitary instruction '{non_unitary_name}'"
            raise ValueError(msg)
        return self.non_unitary_set[non_unitary_name]
