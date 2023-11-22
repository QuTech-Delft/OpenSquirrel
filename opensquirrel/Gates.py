from typing import Tuple

import numpy as np

from opensquirrel.Common import ArgType


class Semantic:
    pass


class SingleQubitAxisAngleSemantic(Semantic):
    def __init__(self, axis: Tuple[float, float, float], angle: float, phase: float):
        self.axis = self._normalize(np.array(axis).astype(np.float64))
        self.angle = angle
        self.phase = phase

    def _normalize(self, axis):
        norm = np.linalg.norm(axis)
        axis /= norm
        return axis


class MultiQubitMatrixSemantic(Semantic):
    def __init__(self, matrix: np.ndarray):
        self.matrix = matrix


class ControlledSemantic(MultiQubitMatrixSemantic):
    def __init__(self, numberOfControlQubits: int, matrix: np.ndarray):
        pass  # TODO


def queryEntry(gatesDict: dict, gateName: str):
    if gateName not in gatesDict:
        raise Exception(f"Unknown gate or alias of gate: `{gateName}`")

    entry = gatesDict[gateName]

    if isinstance(entry, str):
        return queryEntry(gatesDict, entry)

    return entry


def querySemantic(gatesDict: dict, gateName: str, *gateArgs):
    signature = querySignature(gatesDict, gateName)
    assert len(gateArgs) == sum(1 for t in signature if t != ArgType.QUBIT)

    entry = queryEntry(gatesDict, gateName)

    assert "semantic" in entry, f"Gate semantic not defined for gate: `{gateName}`"

    semantic = entry["semantic"]

    if isinstance(semantic, Semantic):
        assert len(gateArgs) == 0, f"Gate `{gateName}` accepts no argument"

        return semantic

    return semantic(*gateArgs)  # TODO: nice error when args don't match? But should be already checked by typer


def querySignature(gatesDict: dict, gateName: str):
    entry = queryEntry(gatesDict, gateName)

    assert "signature" in entry, f"Gate signature not defined for gate: `{gateName}`"

    signature = entry["signature"]

    return signature
