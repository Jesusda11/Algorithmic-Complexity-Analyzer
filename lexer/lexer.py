import re
from .token import Token, TokenType


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.length = len(text)

        # Palabras reservadas
        self.reserved = {
            "begin": TokenType.BEGIN,
            "end": TokenType.END,
            "if": TokenType.IF,
            "then": TokenType.THEN,
            "else": TokenType.ELSE,
            "for": TokenType.FOR,
            "to": TokenType.TO,
            "while": TokenType.WHILE,
            "do": TokenType.DO,
            "repeat": TokenType.REPEAT,
            "until": TokenType.UNTIL,
            "call": TokenType.CALL,
            "return": TokenType.RETURN, 
            "class": TokenType.CLASS,
            "null": TokenType.NULL,
            "T": TokenType.TRUE,
            "F": TokenType.FALSE,
            "and": TokenType.AND,
            "or": TokenType.OR,
            "not": TokenType.NOT,
            # Funciones de strings
            "length": TokenType.LENGTH,
            "upper": TokenType.UPPER,
            "lower": TokenType.LOWER,
            "substring": TokenType.SUBSTRING,
            "trim": TokenType.TRIM,
            # Operadores especiales
            "mod": TokenType.MOD,
            "div": TokenType.DIV_INT,
            "procedure": TokenType.PROCEDURE,
            # AGREGAR ESTAS 4 LÍNEAS:
            "grafo": TokenType.GRAFO,
            "nodos": TokenType.NODOS,
            "aristas": TokenType.ARISTAS,
            "pesos": TokenType.PESOS,
            "dirigido": TokenType.DIRIGIDO,
        }

    def peek(self):
        return self.text[self.pos] if self.pos < self.length else None

    def advance(self):
        ch = self.text[self.pos]
        self.pos += 1

        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1

        return ch

    def make_token(self, type_, value=""):
        return Token(type_, value, self.line, self.col)

    def skip_whitespace(self):
        while self.peek() and self.peek().isspace():
            self.advance()

    def skip_comment(self):
        while self.peek() not in ("\n", None):
            self.advance()

    def lex_number(self):
        start_col = self.col
        num = ""

        while self.peek() and self.peek().isdigit():
            num += self.advance()

        return Token(TokenType.NUMBER, int(num), self.line, start_col)

    def lex_identifier(self):
        start_col = self.col
        ident = ""

        while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
            ident += self.advance()

        key = ident.lower()

        if key in self.reserved:
            return Token(self.reserved[key], ident, self.line, start_col)

        return Token(TokenType.IDENT, ident, self.line, start_col)

    def lex_string(self):
        start_col = self.col
        self.advance()  # skip opening "

        value = ""
        while self.peek() != '"' and self.peek() is not None:
            value += self.advance()

        self.advance()  # closing "
        return Token(TokenType.STRING, value, self.line, start_col)

    def get_next_token(self):
        while self.peek() is not None:

            ch = self.peek()

            # Whitespace
            if ch.isspace():
                if ch == "\n":
                    self.advance()
                    return Token(TokenType.NEWLINE, "\\n", self.line, self.col)
                self.skip_whitespace()
                continue

            # Comments ►
            if ch == "►":
                self.skip_comment()
                continue

            # Assign 🡨
            if ch == "🡨":
                self.advance()
                return Token(TokenType.ASSIGN, "🡨", self.line, self.col)

            # Strings
            if ch == '"':
                return self.lex_string()

            # Numbers
            if ch.isdigit():
                return self.lex_number()

            # Identifiers
            if ch.isalpha():
                return self.lex_identifier()

            # Symbols
            if ch == "[":
                self.advance()
                return Token(TokenType.LBRACKET, "[", self.line, self.col)
            if ch == "]":
                self.advance()
                return Token(TokenType.RBRACKET, "]", self.line, self.col)
            if ch == "(":
                self.advance()
                return Token(TokenType.LPAREN, "(", self.line, self.col)
            if ch == ")":
                self.advance()
                return Token(TokenType.RPAREN, ")", self.line, self.col)
            if ch == "{":
                self.advance()
                return Token(TokenType.LBRACE, "{", self.line, self.col)
            if ch == "}":
                self.advance()
                return Token(TokenType.RBRACE, "}", self.line, self.col)
            if ch == ".":
                self.advance()
                # check range ..
                if self.peek() == ".":
                    self.advance()
                    return Token(TokenType.RANGE, "..", self.line, self.col)
                return Token(TokenType.DOT, ".", self.line, self.col)
            if ch == ",":
                self.advance()
                return Token(TokenType.COMMA, ",", self.line, self.col)

            # ← NUEVO: Soporte directo para símbolos Unicode
            if ch == "≤":
                self.advance()
                return Token(TokenType.LE, "≤", self.line, self.col)
            
            if ch == "≥":
                self.advance()
                return Token(TokenType.GE, "≥", self.line, self.col)
            
            if ch == "≠":
                self.advance()
                return Token(TokenType.NE, "≠", self.line, self.col)

            # Relational operators
            if ch == "<":
                self.advance()
                if self.peek() == "=":
                    self.advance()
                    return Token(TokenType.LE, "<=", self.line, self.col)
                return Token(TokenType.LT, "<", self.line, self.col)
            if ch == ">":
                self.advance()
                if self.peek() == "=":
                    self.advance()
                    return Token(TokenType.GE, ">=", self.line, self.col)
                return Token(TokenType.GT, ">", self.line, self.col)
            if ch == "=":
                self.advance()
                return Token(TokenType.EQ, "=", self.line, self.col)

            # Arithmetic
            if ch == "+":
                self.advance()
                return Token(TokenType.PLUS, "+", self.line, self.col)
            if ch == "-":
                self.advance()
                return Token(TokenType.MINUS, "-", self.line, self.col)
            if ch == "*":
                self.advance()
                return Token(TokenType.MULT, "*", self.line, self.col)
            if ch == "/":
                self.advance()
                return Token(TokenType.DIV, "/", self.line, self.col)

            # Operadores techo y piso
            if ch == "┌":
                self.advance()
                return Token(TokenType.CEIL, "┌", self.line, self.col)

            if ch == "┐":
                self.advance()
                return Token(TokenType.CEIL_END, "┐", self.line, self.col)

            if ch == "└":
                self.advance()
                return Token(TokenType.FLOOR, "└", self.line, self.col)

            if ch == "┘":
                self.advance()
                return Token(TokenType.FLOOR_END, "┘", self.line, self.col)

            raise Exception(f"Caracter inesperado '{ch}' en línea {self.line}, columna {self.col}")

        return Token(TokenType.EOF, "", self.line, self.col)

    def tokenize(self):
        tokens = []
        tok = self.get_next_token()
        while tok.type != TokenType.EOF:
            tokens.append(tok)
            tok = self.get_next_token()

        tokens.append(tok)
        return tokens