# token.py

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
    LENGTH = "LENGTH"

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

    DOT = "DOT"  # .
    COMMA = "COMMA"  # ,
    RANGE = "RANGE"  # ..

    COMMENT = "COMMENT"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


class Token:
    def __init__(self, type_, value, line, col):
        self.type = type_
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"Token({self.type}, {self.value}, line={self.line}, col={self.col})"
