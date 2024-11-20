from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opensquirrel.ir import Gate, NonUnitary


class InstructionLibrary:
    def __init__(
        self,
        gate_set: Mapping[str, Callable[..., Gate]],
        non_unitary_set: Mapping[str, Callable[..., NonUnitary]],
    ) -> None:
        self.gate_set = gate_set
        self.non_unitary_set = non_unitary_set

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
