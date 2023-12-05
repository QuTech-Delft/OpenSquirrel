from typing import List

from opensquirrel.squirrel_ir import Comment, Gate, SquirrelIR


def replace(squirrel_ir: SquirrelIR, gate_name_to_replace: str, f):
    statement_index = 0
    while statement_index < len(squirrel_ir.statements):
        statement = squirrel_ir.statements[statement_index]

        if isinstance(statement, Comment):
            statement_index += 1
            continue

        if not isinstance(statement, Gate):
            raise Exception("Unsupported")

        if statement.name != gate_name_to_replace:
            statement_index += 1
            continue

        # FIXME: handle case where if f is not a function but directly a list.

        replacement: List[Gate] = f(*statement.arguments)
        squirrel_ir.statements[statement_index : statement_index + 1] = replacement
        statement_index += len(replacement)

        # TODO: Here, check that the semantic of the replacement is the same!
        # For this, need to update the simulation capabilities.

        # TODO: Do we allow skipping the replacement, based on arguments?
