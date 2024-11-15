from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opensquirrel.ir import Gate, NonGate


class InstructionLibrary:
    def __init__(
        self,
        gate_set: Mapping[str, Callable[..., Gate]],
        non_gate_set: Mapping[str, Callable[..., NonGate]],
    ) -> None:
        self.gate_set = gate_set
        self.non_gate_set = non_gate_set

    def get_gate_f(self, gate_name: str) -> Callable[..., Gate]:
        if gate_name not in self.gate_set:
            msg = f"unknown unitary instruction '{gate_name}'"
            raise ValueError(msg)
        return self.gate_set[gate_name]

    def get_non_gate_f(self, non_gate_name: str) -> Callable[..., NonGate]:
        if non_gate_name not in self.non_gate_set:
            msg = f"unknown non-unitary instruction '{non_gate_name}'"
            raise ValueError(msg)
        return self.non_gate_set[non_gate_name]
