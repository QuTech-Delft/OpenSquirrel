from __future__ import annotations

import inspect
from collections.abc import Callable
from copy import deepcopy
from functools import partial
from typing import Any

from opensquirrel import instruction_library
from opensquirrel.circuit import Circuit
from opensquirrel.ir import (
    ANNOTATIONS_TO_TYPE_MAP,
    IR,
    Bit,
    BitLike,
    Gate,
    Instruction,
    Qubit,
    QubitLike,
    is_bit_like_annotation as ir_is_bit_like_annotation,
    is_qubit_like_annotation as ir_is_qubit_like_annotation,
)
from opensquirrel.register_manager import BitRegister, QubitRegister, RegisterManager


def is_qubit_like_annotation(annotation: Any) -> bool:
    from opensquirrel.ir import Qubit
    if isinstance(annotation, str):
        return annotation == "Qubit"
    return annotation == Qubit


def is_bit_like_annotation(annotation: Any) -> bool:
    from opensquirrel.ir import Bit
    if isinstance(annotation, str):
        return annotation == "Bit"
    return annotation == Bit


class CircuitBuilder:
    """
    A builder for quantum circuits.
    Supports dynamic register addition and instruction adding.
    """

    def __init__(self) -> None:
        self.register_manager = RegisterManager()
        self.ir = IR()

    def __getattr__(self, attr: str) -> Callable[..., CircuitBuilder]:
        # Only allow dynamic calls for known instructions
        if attr in instruction_library.gate_set or attr in instruction_library.non_unitary_set:
            return partial(self._add_instruction, attr)
        raise AttributeError(f"'CircuitBuilder' object has no instruction or method '{attr}'")

    def add_register(self, register: BitRegister | QubitRegister) -> None:
        self.register_manager.add_register(register)

    def add_instruction(self, instruction: Instruction) -> CircuitBuilder:
        # Accept a pre-constructed Instruction directly
        self.ir.add_statement(instruction)
        return self

    def _add_instruction(self, name: str, *args: Any) -> CircuitBuilder:
        # Add instruction by name + args, e.g., cb.X(q0)
        if name in instruction_library.gate_set:
            generator = instruction_library.get_gate_f(name)
        elif name in instruction_library.non_unitary_set:
            generator = instruction_library.get_non_unitary_f(name)
        else:
            raise ValueError(f"unknown instruction '{name}'")

        self._check_generator_f_args(generator, name, args)
        inst = generator(*args)
        self.ir.add_statement(inst)
        return self

    def _check_qubit_out_of_bounds_access(self, qubit: QubitLike) -> None:
        index = Qubit(qubit).index
        if index >= self.register_manager.get_qubit_register_size():
            raise IndexError("qubit index is out of bounds")

    def _check_bit_out_of_bounds_access(self, bit: BitLike) -> None:
        index = Bit(bit).index
        if index >= self.register_manager.get_bit_register_size():
            raise IndexError("bit index is out of bounds")

    def _check_generator_f_args(
        self,
        generator_f: Callable[..., Instruction],
        name: str,
        args: tuple[Any, ...],
    ) -> None:
        sig = inspect.signature(generator_f)
        params = list(sig.parameters.values())

        required_params = [
            p for p in params
            if p.default == inspect.Parameter.empty
            and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]

        if len(args) < len(required_params):
            raise TypeError(f"missing argument {len(args)+1} for instruction `{name}`")

        for i, par in enumerate(params):
            expected_type = (
                ANNOTATIONS_TO_TYPE_MAP[par.annotation] if isinstance(par.annotation, str) else par.annotation
            )

            try:
                is_incorrect_type = not isinstance(args[i], expected_type)  # type: ignore
            except TypeError:
                # For typing.Union or similar
                is_incorrect_type = not isinstance(args[i], expected_type.__args__)  # type: ignore

            if is_incorrect_type:
                raise TypeError(
                    f"wrong argument type for instruction `{name}`, got {type(args[i])} but expected {expected_type}"
                )
            if is_qubit_like_annotation(expected_type):
                self._check_qubit_out_of_bounds_access(args[i])
            elif is_bit_like_annotation(expected_type):
                self._check_bit_out_of_bounds_access(args[i])

    def to_circuit(self) -> Circuit:
        return Circuit(deepcopy(self.register_manager), deepcopy(self.ir))

    def add_asm(self, *, backend_name: str, backend_code: str) -> CircuitBuilder:
        self.ir.add_asm(backend_name=backend_name, backend_code=backend_code)
        return self

    def add_gate(self, gate: Gate) -> CircuitBuilder:
        self.ir.add_instruction(gate)
        return self

    def add_non_unitary(self, non_unitary: Instruction) -> CircuitBuilder:
        self.ir.add_instruction(non_unitary)
        return self

    def add_control(self, control: Instruction) -> CircuitBuilder:
        # Assuming IR has add_control, else you can define accordingly
        if hasattr(self.ir, 'add_control'):
            self.ir.add_instruction(control)
        return self
    
    def ctrl(self, gate: Gate, control_qubit: QubitLike) -> CircuitBuilder:
        from opensquirrel.ir import ControlledGate

        controlled = ControlledGate(control_qubit=control_qubit, target_gate=gate)
        self.ir.add_gate(controlled)
        return self


