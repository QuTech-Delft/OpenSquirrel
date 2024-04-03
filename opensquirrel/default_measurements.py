from opensquirrel.squirrel_ir import *


@named_measurement
def measure(q: Qubit) -> Measure:
    return Measure(qubit=q, axis=(0, 0, 1))


@named_measurement
def measure_z(q: Qubit) -> Measure:
    return Measure(qubit=q, axis=(0, 0, 1))


@named_measurement
def measure_y(q: Qubit) -> Measure:
    return Measure(qubit=q, axis=(0, 1, 0))


@named_measurement
def measure_x(q: Qubit) -> Measure:
    return Measure(qubit=q, axis=(1, 0, 0))


default_measurement_set = [measure_x, measure_y, measure_z, measure]
default_measurement_aliases = {
    "measure_x": measure_x,
    "measure_y": measure_y,
    "measure_z": measure_z,
    "measure": measure,
}
