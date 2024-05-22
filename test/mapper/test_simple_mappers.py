from __future__ import annotations

import pytest

from open_squirrel.mapper import HardcodedMapper, IdentityMapper
from open_squirrel.mapper.mapping import Mapping
from open_squirrel.utils.check_passes import check_mapper


class TestIdentityMapper:
    @pytest.fixture(name="mapper")
    def mapper_fixture(self) -> IdentityMapper:
        return IdentityMapper(qubit_register_size=3)

    def test_compliance(self, mapper: IdentityMapper) -> None:
        check_mapper(mapper)

    def test_get_mapping(self, mapper: IdentityMapper) -> None:
        assert mapper.get_mapping() == Mapping([0, 1, 2])


class TestHardcodedMapper:
    @pytest.fixture(name="mapper")
    def mapper_fixture(self) -> HardcodedMapper:
        qubit_register_size = 10
        mapping = Mapping([(i + 1) % qubit_register_size for i in range(qubit_register_size)])
        return HardcodedMapper(qubit_register_size, mapping)

    def test_compliance(self, mapper: HardcodedMapper) -> None:
        check_mapper(mapper)

    def test_get_mapping(self, mapper: HardcodedMapper) -> None:
        assert mapper.get_mapping() == Mapping([1, 2, 3, 4, 5, 6, 7, 8, 9, 0])
