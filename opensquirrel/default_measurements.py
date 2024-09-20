from opensquirrel.ir import Bit, Measure, QubitLike, named_measurement


@named_measurement
def measure(q: QubitLike, b: Bit) -> Measure:
    return Measure(qubit=q, bit=b, axis=(0, 0, 1))


@named_measurement
def measure_z(q: QubitLike, b: Bit) -> Measure:
    return Measure(qubit=q, bit=b, axis=(0, 0, 1))


default_measurement_set = [measure_z, measure]
