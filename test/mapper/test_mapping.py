import pytest

from opensquirrel.mapper.mapping import Mapping


class TestMapping:
    def test_1_physical_qubit(self) -> None:
        Mapping([0])

    def test_2_physical_qubits(self) -> None:
        Mapping([0, 1])

    def test_incorrect(self) -> None:
        with pytest.raises(ValueError, match="the mapping is incorrect"):
            Mapping([0, 2])
