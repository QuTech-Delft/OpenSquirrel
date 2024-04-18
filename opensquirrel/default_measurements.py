from opensquirrel.squirrel_ir import Measure, Qubit, named_measurement


@named_measurement
def measure(q: Qubit) -> Measure:
    return Measure(qubit=q, axis=(0, 0, 1))


@named_measurement
def measure_z(q: Qubit) -> Measure:
    return Measure(qubit=q, axis=(0, 0, 1))


default_measurement_set = [measure_z, measure]
