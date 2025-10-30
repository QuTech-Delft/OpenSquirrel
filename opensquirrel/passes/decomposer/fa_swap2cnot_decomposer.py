# %%
from typing import Any

from opensquirrel import CNOT
from opensquirrel.ir import Gate
from opensquirrel.passes.decomposer.general_decomposer import Decomposer


class SWAP2CNOTDecomposer(Decomposer):
    """Predefined decomposition of SWAP gate to 3 CNOT gates.
    ---x---     ----•---[X]---•----
       |     →      |    |    |
    ---x---     ---[X]---•---[X]---
    Note:
        This decomposition preserves the global phase of the SWAP gate.
    """

    def __init__(self, *args: Any, system_calibration: dict[str, Any] | None = None, **kwargs: Any) -> None:
        self.system_calibration = system_calibration or {}
        super().__init__(*args, **kwargs)

    def decompose(self, gate: Gate) -> list[Gate]:
        if gate.name != "SWAP":
            return [gate]
        qubit0, qubit1 = gate.get_qubit_operands()

        f1 = 1
        f2 = 1
        w1 = self.system_calibration.get(f"q{qubit0.index}q{qubit1.index}", None)
        w2 = self.system_calibration.get(f"q{qubit1.index}q{qubit0.index}", None)
        if w1 and w2:
            v1 = w1.get("CNOT", None)
            v2 = w2.get("CNOT", None)
            if v1 and v2:
                f1 = v1.get("fidelity", 1)
                f2 = v2.get("fidelity", 1)

        if f1 < f2:
            qubit0, qubit1 = qubit1, qubit0
        return [
            CNOT(qubit0, qubit1),
            CNOT(qubit1, qubit0),
            CNOT(qubit0, qubit1),
        ]


if __name__ == "__main__":
    from numpy.random import default_rng
    from ptetools.tools import cprint
    from rich import print as rprint

    from opensquirrel import CNOT, SWAP

    rng = default_rng()

    gate = SWAP(0, 1)
    decomposer = SWAP2CNOTDecomposer(system_calibration={})
    r = decomposer.decompose(gate)
    rprint(f"Decompose {gate.name}")
    cprint("No configuration")
    rprint(r)
    system_calibration = {}
    for q in (0, 1, 2):
        system_calibration[f"q{q}"] = {"X": {"fidelity": 0.99 + rng.random() / 200, "duration": 100}}
    for q in (0, 1, 2):
        for p in (0, 1, 2):
            if q == p:
                continue
            system_calibration[f"q{q}q{p}"] = {
                "CNOT": {"fidelity": 0.99 + (q - p) / 400 + rng.random() / 500, "duration": 80},
                "CZ": {"fidelity": 0.99 + rng.random() / 200, "duration": 120},
            }

    cprint("System calibration")
    rprint(system_calibration)

    decomposer = SWAP2CNOTDecomposer(system_calibration=system_calibration)
    r = decomposer.decompose(gate)
    cprint("With configuration")
    rprint(r)
