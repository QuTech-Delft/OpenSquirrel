import re

import pytest

from opensquirrel.passes.mapper.mapping import Mapping


class TestMapping:
    def test_1_physical_qubit(self) -> None:
        Mapping([0])

    def test_2_physical_qubits(self) -> None:
        Mapping([0, 1])

    def test_incorrect(self) -> None:
        msg = re.escape("the mapping Mapping({0: 0, 1: 2}) is incorrect")
        with pytest.raises(ValueError, match=msg):
            Mapping([0, 2])
