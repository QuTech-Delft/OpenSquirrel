from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from opensquirrel.circuit import Circuit


class Analyzer(ABC):
    def __init__(self, **kwargs: Any) -> None: ...

    @abstractmethod
    def analyze(self, circuit: Circuit) -> dict[str, Any]: ...
