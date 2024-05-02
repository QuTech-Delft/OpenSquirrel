from typing import Dict, List


class Mapping:
    """A Mapping is a dictionary where:
       - the keys are virtual qubit indices (from 0 to virtual_qubit_register_size-1), and
       - the values are physical qubit indices.

    Args:
        physical_qubit_register: a list of physical qubit indices.

    Raises:
        ValueError: If the mapping is incorrect.
    """

    def __init__(self, physical_qubit_register: List[int]) -> None:
        self.data: Dict[int, int] = dict(enumerate(physical_qubit_register))
        if (self.data.keys()) != set(self.data.values()):
            raise ValueError("The mapping is incorrect.")

    def __eq__(self, other):
        return self.data == other.data

    def __getitem__(self, key: int) -> int:
        return self.data[key]

    def size(self) -> int:
        return len(self.data)
