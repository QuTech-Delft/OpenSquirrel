"""This module contains all custom exception used by ``OpenSquirrel``."""

from typing import Any


class UnsupportedGateError(Exception):
    """Should be raised when a gate is not supported."""

    def __init__(self, gate: Any, *args: Any) -> None:
        """Init of the ``UnsupportedGateError``.

        Args:
            gate: Gate that is not supported.
        """
        super().__init__(f"{gate} not supported", *args)


class ExporterError(Exception):
    """Should be raised when a circuit cannot be exported to the desired output format."""


class NoRoutingPathError(Exception):
    """Should be raised when no routing path is available between qubits."""

    def __init__(self, message: str, *args: Any) -> None:
        """Init of the ``NoRoutingPathError``.

        Args:
            message: Error message.
        """
        super().__init__(message, *args)
