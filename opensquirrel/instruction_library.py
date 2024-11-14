from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opensquirrel.ir import Gate, NonGate


class InstructionLibrary:
    def __init__(
        self,
        gate_set: Iterable[Callable[..., Gate]],
        non_gate_set: Iterable[Callable[..., NonGate]],
        gate_aliases: Mapping[str, Callable[..., Gate]],
    ) -> None:
        self.gate_set = gate_set
        self.non_gate_set = non_gate_set
        self.gate_aliases = gate_aliases

    def get_gate_f(self, gate_name: str) -> Callable[..., Gate]:
        try:
            generator_f = next(f for f in self.gate_set if f.__name__ == gate_name)
        except StopIteration as exc:
            if gate_name not in self.gate_aliases:
                msg = f"unknown unitary instruction '{gate_name}'"
                raise ValueError(msg) from exc
            generator_f = self.gate_aliases[gate_name]
        return generator_f

    def get_non_gate_f(self, non_gate_name: str) -> Callable[..., NonGate]:
        try:
            return next(f for f in self.non_gate_set if f.__name__ == non_gate_name)
        except StopIteration as exc:
            msg = f"unknown non-unitary instruction `{non_gate_name}`"
            raise ValueError(msg) from exc
