from __future__ import annotations

from typing import Any


class Mapping:
    """A Mapping is a dictionary where:
       - the keys are virtual qubit indices (from 0 to virtual_qubit_register_size-1), and
       - the values are physical qubit indices.

    Args:
        physical_qubit_register: a list of physical qubit indices.

    Raises:
        ValueError: If the mapping is incorrect.
    """

    def __init__(self, physical_qubit_register: list[int]) -> None:
        self.data: dict[int, int] = dict(enumerate(physical_qubit_register))
        if (self.data.keys()) != set(self.data.values()):
            msg = "the mapping is incorrect"
            raise ValueError(msg)

    def __eq__(self, other: Any) -> bool:
        if len(self.data) != len(other.data):
            return False

        if set(self.data.keys()) != set(other.data.keys()):
            return False

        for key in self.data:
            if self.data[key] != other.data[key]:
                return False

        if self.data != other.data:
            return False

        return self.data == other.data

    def __getitem__(self, key: int) -> int:
        return self.data[key]

    def __len__(self) -> int:
        return len(self.data)

    def size(self) -> int:
        return len(self.data)

    def items(self) -> list[tuple[int, int]]:
        return list(self.data.items())

    def keys(self) -> list[int]:
        return list(self.data.keys())

    def values(self) -> list[int]:
        return list(self.data.values())
