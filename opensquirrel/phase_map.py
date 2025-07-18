import numpy as np

from opensquirrel.ir import Qubit, QubitLike


class PhaseMap:
    def __init__(self, qubit_register_size: int) -> None:
        """Initialize a PhaseMap object."""

        self.qubit_phase_map = np.zeros(qubit_register_size, dtype=np.float64)

    def __contains__(self, qubit: QubitLike) -> bool:
        """Checks if qubit is in the phase map."""
        return qubit in self.qubit_phase_map

    def add_qubit_phase(self, qubit: QubitLike, phase: np.float64) -> None:
        self.qubit_phase_map[Qubit(qubit).index] += phase

    def get_qubit_phase(self, qubit: QubitLike) -> np.float64:
        return np.float64(self.qubit_phase_map[Qubit(qubit).index])
