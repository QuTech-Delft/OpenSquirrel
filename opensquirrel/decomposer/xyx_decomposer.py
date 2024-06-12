from __future__ import annotations

from collections.abc import Iterable

from opensquirrel.decomposer.aba_decomposer import ABADecomposer
from opensquirrel.default_gates import Rx, Ry


class XYXDecomposer(ABADecomposer):
    def __init__(self):
        ABADecomposer.__init__(self, Rx, Ry)

    def get_decomposition_angles(self, alpha: float, axis: Iterable[float]) -> tuple[float, float, float]:
        return ABADecomposer.get_decomposition_angles(alpha, axis)
