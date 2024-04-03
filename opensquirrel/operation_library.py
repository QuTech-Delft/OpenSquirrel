class OperationLibrary:
    pass


class GateLibrary(OperationLibrary):
    def __init__(self, gate_set, gate_aliases):
        self.gate_set = gate_set
        self.gate_aliases = gate_aliases

    def get_gate_f(self, gate_name: str):
        try:
            generator_f = next(f for f in self.gate_set if f.__name__ == gate_name)
        except StopIteration:
            if gate_name not in self.gate_aliases:
                raise Exception(f"Unknown gate `{gate_name}`")
            generator_f = self.gate_aliases[gate_name]
        return generator_f


class MeasurementLibrary(OperationLibrary):
    def __init__(self, measurement_set, measurement_aliases):
        self.measurement_set = measurement_set
        self.measurement_aliases = measurement_aliases

    def get_measurement_f(self, measurement_name: str):
        try:
            generator_f = next(f for f in self.measurement_set if f.__name__ == measurement_name)
        except StopIteration:
            if measurement_name not in self.measurement_aliases:
                raise Exception(f"Unknown measurement `{measurement_name}`")
            generator_f = self.measurement_aliases[measurement_name]
        return generator_f
