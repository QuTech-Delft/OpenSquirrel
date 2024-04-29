from __future__ import annotations

from opensquirrel.squirrel_ir import Gate


def filter_out_identities(l: list[Gate]):
    return [g for g in l if not g.is_identity()]
