"""Init file for the validator passes."""

from opensquirrel.passes.validator.general_validator import Validator
from opensquirrel.passes.validator.native_gate_validator import NativeGateValidator

__all__ = ["NativeGateValidator", "Validator"]
