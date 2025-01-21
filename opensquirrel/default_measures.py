from opensquirrel.ir import Bit, Measure, QubitLike, named_measure


@named_measure
def measure(q: QubitLike, b: Bit) -> Measure:
    return Measure(qubit=q, bit=b, axis=(0, 0, 1))


@named_measure
def measure_z(q: QubitLike, b: Bit) -> Measure:
    return Measure(qubit=q, bit=b, axis=(0, 0, 1))


default_measure_set = [measure_z, measure]
