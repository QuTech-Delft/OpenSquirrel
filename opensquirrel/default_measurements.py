from opensquirrel.ir import Bit, Measure, Qubit, named_measurement


@named_measurement
def measure(b: Bit, q: Qubit) -> Measure:
    return Measure(bit=b, qubit=q, axis=(0, 0, 1))


@named_measurement
def measure_z(b: Bit, q: Qubit) -> Measure:
    return Measure(bit=b, qubit=q, axis=(0, 0, 1))


default_measurement_set = [measure_z, measure]
