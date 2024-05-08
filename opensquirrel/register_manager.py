from opensquirrel.mapper import Mapper


class RegisterManager:
    """The RegisterManager class holds:
    - the (virtual) qubit and bit registers size and names, and
    - the mapping between the (virtual) qubit register and the physical qubit register.
    """

    # TODO:
    # In the future, when variables of different types can be defined (e.g. float q)
    # we will have to prevent a variable being called 'q' or 'b'.
    # A possible way to do this is to introduce variable name mangling in the IR
    # (e.g., store 'float q' as 'float _float__q')
    _default_qubit_register_name = "q"
    _default_bit_register_name = "b"

    def __init__(
        self,
        qubit_register_size: int,
        qubit_register_name: str = _default_qubit_register_name,
        bit_register_name: str = _default_bit_register_name,
    ) -> None:
        self.qubit_register_size = qubit_register_size
        self.bit_register_size = qubit_register_size
        self.qubit_register_name = qubit_register_name
        self.bit_register_name = bit_register_name

    def __eq__(self, other):
        return (
            self.qubit_register_size == other.qubit_register_size
            and self.qubit_register_name == other.qubit_register_name
            and self.bit_register_size == other.bit_register_size
            and self.bit_register_name == other.bit_register_name
        )
