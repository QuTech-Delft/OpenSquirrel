import numpy as np
from numpy.typing import NDArray

from opensquirrel.ir import QubitLike


class PhaseMap:
    def __init__(self, phase_map: NDArray[np.complex128]) -> None:
        """Initialize a PhaseMap object."""
        self.qubit_phase_map = phase_map

    def __contains__(self, qubit: QubitLike) -> bool:
        """Checks if qubit is in the phase map."""
        return qubit in self.qubit_phase_map

    def add_qubit_phase(self, qubit: QubitLike, phase: np.complex128) -> None:
        from opensquirrel.ir import Qubit

        self.qubit_phase_map[Qubit(qubit).index] += phase

    def get_qubit_phase(self, qubit: QubitLike) -> np.complex128:
        from opensquirrel.ir import Qubit

        return np.complex128(self.qubit_phase_map[Qubit(qubit).index])
