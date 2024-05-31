from __future__ import annotations

from abc import ABC
from collections.abc import Callable, Iterable, Mapping

from opensquirrel.squirrel_ir import Gate, Measure


class InstructionLibrary(ABC):
    """Abstract base class for instruction libraries."""


class GateLibrary(InstructionLibrary):
    def __init__(
        self, gate_set: Iterable[Callable[..., Gate]], gate_aliases: Mapping[str, Callable[..., Gate]]
    ) -> None:
        self.gate_set = gate_set
        self.gate_aliases = gate_aliases

    def get_gate_f(self, gate_name: str) -> Callable[..., Gate]:
        try:
            generator_f = next(f for f in self.gate_set if f.__name__ == gate_name)
        except StopIteration as exc:
            if gate_name not in self.gate_aliases:
                raise ValueError(f"Unknown instruction `{gate_name}`") from exc
            generator_f = self.gate_aliases[gate_name]
        return generator_f


class MeasurementLibrary(InstructionLibrary):
    def __init__(self, measurement_set: Iterable[Callable[..., Measure]]) -> None:
        self.measurement_set = measurement_set

    def get_measurement_f(self, measurement_name: str) -> Callable[..., Measure]:
        try:
            generator_f = next(f for f in self.measurement_set if f.__name__ == measurement_name)
            return generator_f
        except StopIteration as exc:
            raise ValueError(f"Unknown instruction `{measurement_name}`") from exc
