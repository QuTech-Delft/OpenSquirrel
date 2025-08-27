from opensquirrel.ir import Qubit, QubitLike, AxisLike
from opensquirrel.ir.semantics.canonical_gate import CanonicalGate

class TwoQubitGate(CanonicalGate):
    
    def __init__(self, qubit_0: QubitLike, qubit_1: QubitLike, canonical_axis: AxisLike, name: str="TwoQubitGate") -> None:
        CanonicalGate.__init__(self, qubit_0, qubit_1, name)
        self.qubit_0 = Qubit(qubit_0)
        self.qubit_1 = Qubit(qubit_1)
        self.canonical_gate = CanonicalGate(self.qubit_0, self.qubit_1, canonical_axis)
