"""This module contains all custom exception used by ``OpenSquirrel``."""

from typing import Any


class UnsupportedGateError(Exception):
    """Should be raised when a gate is not supported."""

    def __init__(self, gate: Any, *args) -> None:
        """Init of the ``UnsupportedGateError``.

        Args:
            gate: Gate that is not supported.
        """
        self.unsupported_gate = gate
        super().__init__(f"The following gate is not supported: {gate}.", *args)


class ExportError(Exception):
    """Should be raised when a gate is not supported by the exporter."""
