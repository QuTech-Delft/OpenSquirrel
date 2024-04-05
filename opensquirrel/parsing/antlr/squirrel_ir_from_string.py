import antlr4

from opensquirrel.parsing.antlr.generated import CQasm3Lexer, CQasm3Parser
from opensquirrel.parsing.antlr.qubit_range_checker import QubitRangeChecker
from opensquirrel.parsing.antlr.squirrel_error_handler import SquirrelErrorHandler
from opensquirrel.parsing.antlr.squirrel_ir_creator import SquirrelIRCreator
from opensquirrel.parsing.antlr.type_checker import TypeChecker
from opensquirrel.squirrel_ir import SquirrelIR


def antlr_tree_from_string(s: str):
    input_stream = antlr4.InputStream(s)

    lexer = CQasm3Lexer.CQasm3Lexer(input_stream)

    stream = antlr4.CommonTokenStream(lexer)

    parser = CQasm3Parser.CQasm3Parser(stream)

    parser.removeErrorListeners()
    parser.addErrorListener(SquirrelErrorHandler())

    return parser.prog()


def type_check_antlr_tree(tree, gate_set, gate_aliases, measurement_set, measurement_aliases):
    type_checker = TypeChecker(gate_set, gate_aliases, measurement_set, measurement_aliases)
    type_checker.visit(tree)  # FIXME: return error instead of throwing?


def check_qubit_ranges_of_antlr_tree(tree):
    qubit_range_checker = QubitRangeChecker()
    qubit_range_checker.visit(tree)  # FIXME: return error instead of throwing?


def squirrel_ir_from_string(s: str, gate_set, gate_aliases, measurement_set, measurement_aliases):
    """
    ANTLR parsing entrypoint.
    Performs type checking based on provided gate semantics and check that the qubit indices are valid.
    Creates the IR where each gate node is mapped to its semantic function and arguments.

    Args:
        gate_set: The set of supported gate semantics.
        gate_aliases: Dictionary mapping extra gate names to their semantic.
        measurement_set: The set of supported measurement semantics.
        measurement_aliases: Dictionary mapping extra measurement names to their semantic.

    Returns:
        A corresponding SquirrelIR object. Throws in case of parsing error.
    """
    tree = antlr_tree_from_string(s)

    type_check_antlr_tree(
        tree,
        gate_set=gate_set,
        gate_aliases=gate_aliases,
        measurement_set=measurement_set,
        measurement_aliases=measurement_aliases,
    )

    check_qubit_ranges_of_antlr_tree(tree)

    squirrel_ir_creator = SquirrelIRCreator(
        gate_set=gate_set,
        gate_aliases=gate_aliases,
        measurement_set=measurement_set,
        measurement_aliases=measurement_aliases,
    )

    return squirrel_ir_creator.visit(tree)
