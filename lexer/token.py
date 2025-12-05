class TokenType:
    # Palabras reservadas
    BEGIN = "BEGIN"
    END = "END"
    IF = "IF"
    THEN = "THEN"
    ELSE = "ELSE"
    FOR = "FOR"
    TO = "TO"
    WHILE = "WHILE"
    DO = "DO"
    REPEAT = "REPEAT"
    UNTIL = "UNTIL"
    CALL = "CALL"
    CLASS = "CLASS"
    NULL = "NULL"
    TRUE = "T"
    FALSE = "F"
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    # Funciones de strings
    LENGTH = "LENGTH"
    UPPER = "UPPER"
    LOWER = "LOWER"
    SUBSTRING = "SUBSTRING"
    TRIM = "TRIM"

    # Otros tokens
    IDENT = "IDENT"  # nombres de variables, clases, objetos
    NUMBER = "NUMBER"  # 123, 45, etc
    STRING = "STRING"  # "hola"

    ASSIGN = "ASSIGN"  # 🡨
    PLUS = "PLUS"  # +
    MINUS = "MINUS"  # -
    MULT = "MULT"  # *
    DIV = "DIV"  # /
    MOD = "MOD"  # mod
    DIV_INT = "DIV_INT"  # div

    LT = "LT"  # <
    GT = "GT"  # >
    LE = "LE"  # ≤
    GE = "GE"  # ≥
    EQ = "EQ"  # =
    NE = "NE"  # ≠

    LBRACKET = "LBRACKET"  # [
    RBRACKET = "RBRACKET"  # ]
    LPAREN = "LPAREN"  # (
    RPAREN = "RPAREN"  # )
    LBRACE = "LBRACE"  # {
    RBRACE = "RBRACE"  # }

    DOT = "DOT"  # .
    COMMA = "COMMA"  # ,
    RANGE = "RANGE"  # ..

    COMMENT = "COMMENT"
    NEWLINE = "NEWLINE"
    EOF = "EOF"
    PROCEDURE = "PROCEDURE"

    CEIL = "CEIL"  # ┌
    CEIL_END = "CEIL_END"  # ┐

    FLOOR = "FLOOR"  # └┘
    FLOOR_END = "FLOOR_END"  # ┘

    GRAFO = "GRAFO"
    NODOS = "NODOS"
    ARISTAS = "ARISTAS"
    PESOS = "PESOS"
    DIRIGIDO = "DIRIGIDO"

    RETURN = "RETURN"  # RETURN statement

class Token:
    def __init__(self, type, value, line, col):
        self.type = type
        self.value = value
        self.line = line
        self.col = col

    def repr(self):
        return f"Token({self.type}, {self.value}, line={self.line}, col={self.col})"