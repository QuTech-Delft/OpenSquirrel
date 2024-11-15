from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opensquirrel.ir import Directive, Gate, Measure, Reset


class InstructionLibrary:
    """Base class for instruction libraries."""


class GateLibrary(InstructionLibrary):
    def __init__(
        self,
        gate_set: Iterable[Callable[..., Gate]],
        gate_aliases: Mapping[str, Callable[..., Gate]],
    ) -> None:
        self.gate_set = gate_set
        self.gate_aliases = gate_aliases

    def get_gate_f(self, gate_name: str) -> Callable[..., Gate]:
        try:
            generator_f = next(f for f in self.gate_set if f.__name__ == gate_name)
        except StopIteration as exc:
            if gate_name not in self.gate_aliases:
                msg = f"unknown instruction '{gate_name}'"
                raise ValueError(msg) from exc
            generator_f = self.gate_aliases[gate_name]
        return generator_f


class MeasureLibrary(InstructionLibrary):
    def __init__(self, measure_set: Iterable[Callable[..., Measure]]) -> None:
        self.measure_set = measure_set

    def get_measure_f(self, measure_name: str) -> Callable[..., Measure]:
        try:
            return next(f for f in self.measure_set if f.__name__ == measure_name)
        except StopIteration as exc:
            msg = f"unknown instruction `{measure_name}`"
            raise ValueError(msg) from exc


class ResetLibrary(InstructionLibrary):
    def __init__(self, reset_set: Iterable[Callable[..., Reset]]) -> None:
        self.reset_set = reset_set

    def get_reset_f(self, reset_name: str) -> Callable[..., Reset]:
        try:
            return next(f for f in self.reset_set if f.__name__ == reset_name)
        except StopIteration as exc:
            msg = f"unknown instruction `{reset_name}`"
            raise ValueError(msg) from exc


class DirectiveLibrary(InstructionLibrary):
    def __init__(self, directive_set: Iterable[Callable[..., Directive]]) -> None:
        self.directive_set = directive_set

    def get_directive_f(self, directive_name: str) -> Callable[..., Directive]:
        try:
            return next(f for f in self.directive_set if f.__name__ == directive_name)
        except StopIteration as exc:
            msg = f"unknown instruction `{directive_name}`"
            raise ValueError(msg) from exc
