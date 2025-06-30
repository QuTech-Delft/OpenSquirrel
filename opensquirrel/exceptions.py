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
