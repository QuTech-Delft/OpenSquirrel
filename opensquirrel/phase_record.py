from opensquirrel.ir import Qubit, QubitLike


class PhaseRecord:
    def __init__(self, qubit_register_size: int) -> None:
        """Initialize a PhaseMap object."""

        self.qubit_phase_record = [0.0] * qubit_register_size

    def __contains__(self, qubit: QubitLike) -> bool:
        """Checks if qubit is in the phase map."""
        return qubit in self.qubit_phase_record

    def add_qubit_phase(self, qubit: QubitLike, phase: float) -> None:
        self.qubit_phase_record[Qubit(qubit).index] += phase

    def get_qubit_phase(self, qubit: QubitLike) -> float:
        return float(self.qubit_phase_record[Qubit(qubit).index])
