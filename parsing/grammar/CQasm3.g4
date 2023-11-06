grammar CQasm3;

stateSep: ( ';' | '\r\n' | '\n' )+ ;

prog:   stateSep? VERSION '3.0' stateSep qubitRegisterDeclaration (stateSep gateApplication)* stateSep? EOF ;

qubitRegisterDeclaration: 'qubit[' INT ']' ID ;

gateApplication: ID expr (',' expr)* ;

expr:     ID '[' INT ']'                    # Qubit
      |   ID '[' INT (',' INT )* ']'        # Qubits
      |   ID '[' INT ':' INT ']'            # QubitRange
      |   INT                               # IntLiteral
      |   '-' INT                           # NegatedIntLiteral
      |   FLOAT                             # FloatLiteral
      |   '-' FLOAT                         # NegatedFloatLiteral
      ;

VERSION: 'version' ;
ID  :   [a-zA-Z][a-zA-Z0-9]* ;
FLOAT :   [0-9]+[.][0-9]* ;
INT :   [0-9]+ ;
WS  :   [ \t]+ -> skip ;
COMMENT  :   '//' ~[\r\n]* -> skip ;
MULTILINE_COMMENT  :   '/*' .*? '*/' -> skip ;