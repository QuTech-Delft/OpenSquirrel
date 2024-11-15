from opensquirrel.ir import Barrier, QubitLike, named_directive


@named_directive
def barrier(q: QubitLike) -> Barrier:
    return Barrier(q)


default_directive_set = [barrier]
