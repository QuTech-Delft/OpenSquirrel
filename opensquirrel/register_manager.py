from typing import NewType

from opensquirrel.mapper.simple_mappers import IdentityMapper


class RegisterManager:
    """The RegisterManager class holds:
       - the (virtual) qubit and bit registers size and names, and
       - the mapping between the (virtual) qubit register and the physical qubit register.
    """

    _default_qubit_register_name = "q"
    _default_bit_register_name = "b"

    def __init__(
        self,
        qubit_register_size: int,
        bit_register_size: int,
        qubit_register_name: str = _default_qubit_register_name,
        bit_register_name: str = _default_bit_register_name
    ) -> None:
        self.qubit_register_size = qubit_register_size
        self.bit_register_size = bit_register_size
        self.qubit_register_name = qubit_register_name
        self.bit_register_name = bit_register_name
        self.mapping = IdentityMapper(register_size).get_mapping()

    def get_physical_qubit_index(self, qubit_index: QubitIndex):
        return self.mapping.data[qubit_index]


QubitIndex = NewType('QubitIndex', int)
PhysicalQubitIndex = NewType('PhysicalQubitIndex', int)
