from __future__ import annotations

import pytest

from opensquirrel.mapper import HardcodedMapper, IdentityMapper
from opensquirrel.squirrel_ir import SquirrelIR
from opensquirrel.utils.check_passes import check_mapper


class TestIdentityMapper:
    @pytest.fixture(name="mapper")
    def mapper_fixture(self) -> IdentityMapper:
        return IdentityMapper()

    def test_compliance(self, mapper: IdentityMapper) -> None:
        check_mapper(mapper)

    def test_mapping(self, mapper: IdentityMapper) -> None:
        squirrel_ir = SquirrelIR(number_of_qubits=3)
        mapping = mapper.map(squirrel_ir)
        assert mapping == {0: 0, 1: 1, 2: 2}


class TestHardcodedMapper:

    @pytest.fixture(name="mapper")
    def mapper_fixture(self) -> HardcodedMapper:
        mapping = {i: (i + 1) % 10 for i in range(10)}
        return HardcodedMapper(mapping)

    def test_compliance(self, mapper: HardcodedMapper) -> None:
        check_mapper(mapper)

    def test_mapping(self, mapper: HardcodedMapper) -> None:
        squirrel_ir = SquirrelIR(number_of_qubits=10)
        mapping = mapper.map(squirrel_ir)
        assert mapping == {0: 1, 1: 2, 2: 3, 3: 4, 4: 5, 5: 6, 6: 7, 7: 8, 8: 9, 9: 0}

    @pytest.mark.parametrize("incorrect_mapping", [{0: 0, 1: 0}, {0: 1}])
    def test_errors(self, incorrect_mapping: dict[int, int]) -> None:
        with pytest.raises(ValueError):
            HardcodedMapper(incorrect_mapping)
