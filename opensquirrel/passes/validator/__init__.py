"""Init file for the validator passes."""

from opensquirrel.passes.validator.general_validator import Validator
from opensquirrel.passes.validator.interaction_validator import InteractionValidator
from opensquirrel.passes.validator.primitive_gate_validator import PrimitiveGateValidator

__all__ = ["InteractionValidator", "PrimitiveGateValidator", "Validator"]
