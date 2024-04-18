import inspect
import itertools

import cqasm.v3x as cqasm

from opensquirrel.default_gates import default_gate_aliases, default_gate_set
from opensquirrel.default_measurements import default_measurement_set
from opensquirrel.instruction_library import GateLibrary, MeasurementLibrary
from opensquirrel.squirrel_ir import Float, Int, Qubit, SquirrelIR

_cqasm_type_to_squirrel_type = {
    cqasm.types.QubitArray: Qubit,
    cqasm.values.ConstInt: Int,
    cqasm.values.ConstFloat: Float,
}


class LibqasmIRCreator(GateLibrary, MeasurementLibrary):
    def __init__(
        self,
        gate_set=default_gate_set,
        gate_aliases=default_gate_aliases,
        measurement_set=default_measurement_set,
    ):
        GateLibrary.__init__(self, gate_set, gate_aliases)
        MeasurementLibrary.__init__(self, measurement_set)
        self.squirrel_ir = None

    @staticmethod
    def _get_qubits(cqasm_qubits_expression):
        return [Qubit(index.value) for index in cqasm_qubits_expression.indices]

    @staticmethod
    def _get_literal(cqasm_literal_expression):
        assert type(cqasm_literal_expression) in [cqasm.values.ConstInt, cqasm.values.ConstFloat]

        if isinstance(cqasm_literal_expression, cqasm.values.ConstInt):
            return Int(cqasm_literal_expression.value)

        if isinstance(cqasm_literal_expression, cqasm.values.ConstFloat):
            return Float(cqasm_literal_expression.value)

        return None

    @staticmethod
    def _check_cqasm_type(cqasm_expression, expected_squirrel_type):
        cqasm_type = (
            type(cqasm_expression.variable.typ)
            if isinstance(cqasm_expression, cqasm.values.IndexRef)
            else type(cqasm_expression)
        )

        # The below is already guaranteed by Libqasm, therefore it's just an assert.
        assert _cqasm_type_to_squirrel_type[cqasm_type] == expected_squirrel_type

    @classmethod
    def _get_expanded_squirrel_args(cls, generator_f, cqasm_args):
        parameters = inspect.signature(generator_f).parameters.values()

        ### The below is already guaranteed by LibQasm, therefore it's just an assert.
        assert len(parameters) == len(cqasm_args)
        for cqasm_arg, expected_parameter in zip(cqasm_args, parameters):
            cls._check_cqasm_type(cqasm_expression=cqasm_arg, expected_squirrel_type=expected_parameter.annotation)

        number_of_operands = next(
            len(cqasm_arg.indices)
            for cqasm_arg, expected_parameter in zip(cqasm_args, parameters)
            if expected_parameter.annotation == Qubit
        )

        expanded_args = [
            (
                cls._get_qubits(cqasm_arg)
                if expected_parameter.annotation == Qubit
                else [cls._get_literal(cqasm_arg)] * number_of_operands
            )
            for cqasm_arg, expected_parameter in zip(cqasm_args, parameters)
        ]

        return zip(*expanded_args)

    @staticmethod
    def _get_cqasm_param_type_letters(squirrel_type):
        if squirrel_type == Qubit:
            return "Q", "V"  # "V" is to allow array notations like q[3, 5, 7] and q[3:6]

        if squirrel_type == Float:
            return "f"

        if squirrel_type == Int:
            return "i"

        raise TypeError("Unsupported type")

    def _create_analyzer(self):
        without_defaults = True
        analyzer = cqasm.Analyzer("3.0.0", without_defaults)
        for generator_f in self.gate_set:
            for set_of_letters in itertools.product(
                *(
                    self._get_cqasm_param_type_letters(p.annotation)
                    for p in inspect.signature(generator_f).parameters.values()
                )
            ):
                param_types = "".join(set_of_letters)
                analyzer.register_instruction(generator_f.__name__, param_types)

        for generator_f in self.measurement_set:
            for set_of_letters in itertools.product(
                *(
                    self._get_cqasm_param_type_letters(p.annotation)
                    for p in inspect.signature(generator_f).parameters.values()
                )
            ):
                param_types = "".join(set_of_letters)
                analyzer.register_instruction(generator_f.__name__, param_types)

        return analyzer

    def squirrel_ir_from_string(self, s: str):
        analyzer = self._create_analyzer()

        ast = analyzer.analyze_string(s)

        if isinstance(ast, list):
            raise Exception("Parsing error: " + ", ".join(ast))

        number_of_qubits = ast.qubit_variable_declaration.typ.size

        # FIXME: libqasm should return bytes, not the __repr__ of a bytes object ("b'q'")
        qubit_register_name = ast.qubit_variable_declaration.name[2:-1]

        squirrel_ir = SquirrelIR(number_of_qubits=number_of_qubits, qubit_register_name=qubit_register_name)

        for statement in ast.block.statements:
            if "measure" in statement.name[2:-1]:
                generator_f = self.get_measurement_f(statement.name[2:-1])
            else:
                generator_f = self.get_gate_f(statement.name[2:-1])

            expanded_squirrel_args = LibqasmIRCreator._get_expanded_squirrel_args(generator_f, statement.operands)

            for arg_set in expanded_squirrel_args:
                squirrel_ir.add_gate(generator_f(*arg_set))

        return squirrel_ir
