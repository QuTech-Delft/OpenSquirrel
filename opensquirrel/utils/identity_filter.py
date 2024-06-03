from __future__ import annotations

from collections.abc import Iterable

from opensquirrel.ir import Gate


def filter_out_identities(gates: Iterable[Gate]) -> list[Gate]:
    return [gate for gate in gates if not gate.is_identity()]
