# parser.py

from lexer.token import TokenType


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # -----------------------------
    # UTILIDADES
    # -----------------------------
    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def match(self, type_):
        if self.peek().type == type_:
            return self.advance()
        raise Exception(f"Se esperaba {type_} y se encontró {self.peek()}")

    def optional(self, type_):
        if self.peek().type == type_:
            return self.advance()
        return None

    # -----------------------------
    # ENTRYPOINT
    # -----------------------------
    def parse(self):
        statements = []

        while self.peek().type != TokenType.EOF:
            stmt = self.statement()
            if stmt:
                statements.append(stmt)

            # consumir saltos de línea si hay
            if self.peek().type == TokenType.NEWLINE:
                self.advance()

        return {
            "type": "program",
            "body": statements
        }

    # -----------------------------
    # STATEMENTS
    # -----------------------------
    def statement(self):

        tok = self.peek()

        # FOR
        if tok.type == TokenType.FOR:
            return self.parse_for()

        # IF
        if tok.type == TokenType.IF:
            return self.parse_if()

        # CALL
        if tok.type == TokenType.CALL:
            return self.parse_call()

        # IDENT -> asignación
        if tok.type == TokenType.IDENT:
            return self.parse_assign()

        return None

    # -----------------------------
    # ASSIGN:  x 🡨 y
    # -----------------------------
    def parse_assign(self):
        ident = self.match(TokenType.IDENT)
        self.match(TokenType.ASSIGN)
        expr = self.parse_expression()

        return {
            "type": "assign",
            "target": ident.value,
            "expr": expr
        }

    # -----------------------------
    # CALL:  call f(a, b)
    # -----------------------------
    def parse_call(self):
        self.match(TokenType.CALL)
        func = self.match(TokenType.IDENT)

        self.match(TokenType.LPAREN)

        args = []
        if self.peek().type != TokenType.RPAREN:
            args.append(self.parse_expression())
            while self.optional(TokenType.COMMA):
                args.append(self.parse_expression())

        self.match(TokenType.RPAREN)

        return {
            "type": "call",
            "name": func.value,
            "args": args
        }

    # -----------------------------
    # FOR: for i 🡨 1 to n do begin ... end
    # -----------------------------
    def parse_for(self):
        self.match(TokenType.FOR)
        var = self.match(TokenType.IDENT)
        self.match(TokenType.ASSIGN)
        start = self.parse_expression()
        self.match(TokenType.TO)
        end = self.parse_expression()
        self.match(TokenType.DO)

        body = self.parse_block()

        return {
            "type": "for",
            "var": var.value,
            "start": start,
            "end": end,
            "body": body
        }

    # -----------------------------
    # IF: if (...) then begin ... end else begin ... end
    # -----------------------------
    def parse_if(self):
        self.match(TokenType.IF)
        self.match(TokenType.LPAREN)
        cond = self.parse_expression()
        self.match(TokenType.RPAREN)

        self.match(TokenType.THEN)
        then_block = self.parse_block()

        self.match(TokenType.ELSE)
        else_block = self.parse_block()

        return {
            "type": "if",
            "cond": cond,
            "then": then_block,
            "else": else_block
        }

    # -----------------------------
    # BLOCK: begin ... end
    # -----------------------------
    def parse_block(self):
        self.match(TokenType.BEGIN)
        statements = []

        while self.peek().type != TokenType.END:
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
            if self.peek().type == TokenType.NEWLINE:
                self.advance()

        self.match(TokenType.END)

        return {
            "type": "block",
            "body": statements
        }

    # -----------------------------
    # EXPRESIONES (versión mínima)
    # -----------------------------
    def parse_expression(self):
        tok = self.peek()

        if tok.type == TokenType.NUMBER:
            return {"type": "number", "value": self.advance().value}

        if tok.type == TokenType.IDENT:
            return {"type": "var", "value": self.advance().value}

        raise Exception(f"Expresión no válida comenzando en {tok}")
