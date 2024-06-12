from __future__ import annotations

from collections.abc import Iterable

from opensquirrel.default_gates import Ry, Rz
from opensquirrel.decomposer.aba_decomposer import ABADecomposer


class ZYZDecomposer(ABADecomposer):
    def __init__(self):
        ABADecomposer.__init__(self, Rz, Ry)

    def get_zyz_decomposition_angles(alpha: float, axis: Iterable[float]) -> tuple[float, float, float]:
        return ABADecomposer.get_decomposition_angles(alpha, axis)
