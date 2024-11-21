from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from opensquirrel.default_instructions import default_gate_set, default_non_unitary_set

if TYPE_CHECKING:
    from opensquirrel.ir import Gate, NonUnitary


gate_set = default_gate_set
non_unitary_set = default_non_unitary_set


def get_gate_f(gate_name: str) -> Callable[..., Gate]:
    if gate_name not in gate_set:
        msg = f"unknown gate '{gate_name}'"
        raise ValueError(msg)
    return gate_set[gate_name]


def get_non_unitary_f(non_unitary_name: str) -> Callable[..., NonUnitary]:
    if non_unitary_name not in non_unitary_set:
        msg = f"unknown non-unitary instruction '{non_unitary_name}'"
        raise ValueError(msg)
    return non_unitary_set[non_unitary_name]
