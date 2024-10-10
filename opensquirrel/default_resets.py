from opensquirrel.ir import QubitLike, Reset, named_reset


@named_reset
def reset(q: QubitLike) -> Reset:
    return Reset(qubit=q)


default_reset_set = [reset]
