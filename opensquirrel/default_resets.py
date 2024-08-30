from opensquirrel.ir import Qubit, Reset, named_reset


@named_reset
def reset(q: Qubit) -> Reset:
    return Reset(qubit=q)


default_reset_set = [reset]
