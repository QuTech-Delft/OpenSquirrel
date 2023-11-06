from antlr4.error.ErrorListener import ErrorListener as Antlr4ErrorListener

class SquirrelParseException(Exception):
    pass

class SquirrelErrorHandler(Antlr4ErrorListener) :
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        stack = recognizer.getRuleInvocationStack()
        stack.reverse()
        raise SquirrelParseException(f"Parsing error at {line}:{column}: {msg}")