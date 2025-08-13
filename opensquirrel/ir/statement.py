from abc import ABC, abstractmethod
from typing import Any

from opensquirrel.ir.expression import Bit, Expression, Qubit, String, SupportsStr
from opensquirrel.ir.ir import IRNode, IRVisitor


class Statement(IRNode, ABC):
    pass


class AsmDeclaration(Statement):
    """``AsmDeclaration`` is used to define an assembly declaration statement in the IR.

    Args:
        backend_name: Name of the backend that is to process the provided backend code.
        backend_code: (Assembly) code to be processed by the specified backend.
    """

    def __init__(
        self,
        backend_name: SupportsStr,
        backend_code: SupportsStr,
    ) -> None:
        self.backend_name = String(backend_name)
        self.backend_code = String(backend_code)
        Statement.__init__(self)

    def accept(self, visitor: IRVisitor) -> Any:
        visitor.visit_statement(self)
        return visitor.visit_asm_declaration(self)


class Instruction(Statement, ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @property
    @abstractmethod
    def arguments(self) -> tuple[Expression, ...]:
        pass

    @abstractmethod
    def get_qubit_operands(self) -> list[Qubit]:
        pass

    @abstractmethod
    def get_bit_operands(self) -> list[Bit]:
        pass
