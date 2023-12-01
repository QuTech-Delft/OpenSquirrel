from typing import Type

from passes.decomposer import Decomposer
from passes.writer import Writer


class Circuit:

    def __init__(self, circuit: str):
        self._ast = "ast_" + circuit

    def decompose(self, decomposer: Type[Decomposer], **kwargs):
        self._ast = decomposer.apply(self._ast, **kwargs)

    def write(self, writer: Type[Writer]):
        return writer.apply(ast=self._ast)
