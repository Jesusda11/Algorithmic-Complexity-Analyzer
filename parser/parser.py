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

    def skip_newlines(self):
        while self.peek().type == TokenType.NEWLINE:
            self.advance()

    # -----------------------------
    # ENTRYPOINT
    # -----------------------------
    def parse(self):
        statements = []

        while self.peek().type != TokenType.EOF:
            self.skip_newlines()

            if self.peek().type == TokenType.EOF:
                break

            stmt = self.statement()
            if stmt:
                statements.append(stmt)

            self.skip_newlines()

        return {"type": "program", "body": statements}

    # -----------------------------
    # STATEMENTS
    # -----------------------------
    def statement(self):

        tok = self.peek()

        if tok.type == TokenType.FOR:
            return self.parse_for()

        if tok.type == TokenType.IF:
            return self.parse_if()

        if tok.type == TokenType.CALL:
            return self.parse_call()

        if tok.type == TokenType.WHILE:
            return self.parse_while()

        if tok.type == TokenType.REPEAT:
            return self.parse_repeat_until()

        if tok.type == TokenType.IDENT:
            return self.parse_assign()

        return None

    # -----------------------------
    # ASSIGN
    # -----------------------------
    def parse_assign(self):
        ident = self.match(TokenType.IDENT)
        self.match(TokenType.ASSIGN)
        expr = self.parse_expression()

        return {"type": "assign", "target": ident.value, "expr": expr}

    # -----------------------------
    # CALL
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

        return {"type": "call", "name": func.value, "args": args}

    # -----------------------------
    # FOR
    # -----------------------------
    def parse_for(self):
        self.match(TokenType.FOR)
        var = self.match(TokenType.IDENT)
        self.match(TokenType.ASSIGN)
        start = self.parse_expression()
        self.match(TokenType.TO)
        end = self.parse_expression()
        self.match(TokenType.DO)

        self.skip_newlines()

        body = self.parse_block()

        return {"type": "for", "var": var.value, "start": start, "end": end, "body": body}

    # -----------------------------
    # IF
    # -----------------------------
    def parse_if(self):
        self.match(TokenType.IF)
        self.match(TokenType.LPAREN)
        cond = self.parse_expression()
        self.match(TokenType.RPAREN)

        self.match(TokenType.THEN)

        self.skip_newlines()

        then_block = self.parse_block()

        self.skip_newlines()

        self.match(TokenType.ELSE)
        self.skip_newlines()

        else_block = self.parse_block()

        return {"type": "if", "cond": cond, "then": then_block, "else": else_block}

    # -----------------------------
    # WHILE
    # -----------------------------
    def parse_while(self):
        self.match(TokenType.WHILE)
        self.match(TokenType.LPAREN)
        cond = self.parse_expression()
        self.match(TokenType.RPAREN)
        self.match(TokenType.DO)

        self.skip_newlines()

        body = self.parse_block()

        return {"type": "while", "cond": cond, "body": body}

    # -----------------------------
    # REPEAT UNTIL
    # -----------------------------
    def parse_repeat_until(self):
        self.match(TokenType.REPEAT)

        self.skip_newlines()

        statements = []

        # El cuerpo del REPEAT no usa BEGIN...END, solo líneas hasta UNTIL
        while self.peek().type not in (TokenType.UNTIL, TokenType.EOF):
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()

        # Aquí debe venir UNTIL
        self.match(TokenType.UNTIL)

        # Ahora debe venir la condición entre paréntesis
        self.match(TokenType.LPAREN)
        cond = self.parse_expression()
        self.match(TokenType.RPAREN)

        return {
            "type": "repeat",
            "body": statements,
            "cond": cond
        }

    # -----------------------------
    # BLOCK
    # -----------------------------
    def parse_block(self):
        self.skip_newlines()

        self.match(TokenType.BEGIN)

        statements = []

        while True:
            self.skip_newlines()

            if self.peek().type == TokenType.END:
                break

            stmt = self.statement()
            if stmt:
                statements.append(stmt)

        self.match(TokenType.END)

        return {"type": "block", "body": statements}

    # -----------------------------
    # EXPRESIONES (mínimas)
    # -----------------------------
    def parse_expression(self):
        node = self.parse_additive()

        # Comparadores: = < > <= >= ≠
        if self.peek().type in (TokenType.GT, TokenType.LT, TokenType.EQ,
                                TokenType.LE, TokenType.GE, TokenType.NE):
            op = self.advance()
            right = self.parse_additive()
            return {"type": "binop", "op": op.type, "left": node, "right": right}

        return node
    
    def parse_additive(self):
        node = self.parse_term()

        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance()
            right = self.parse_term()
            node = {"type": "binop", "op": op.type, "left": node, "right": right}

        return node
    
    def parse_term(self):
        node = self.parse_factor()

        while self.peek().type in (TokenType.MULT, TokenType.DIV,
                                   TokenType.MOD, TokenType.DIV_INT):
            op = self.advance()
            right = self.parse_factor()
            node = {"type": "binop", "op": op.type, "left": node, "right": right}

        return node
    
    def parse_factor(self):
        tok = self.peek()

        if tok.type == TokenType.NUMBER:
            self.advance()
            return {"type": "number", "value": tok.value}

        if tok.type == TokenType.IDENT:
            self.advance()
            return {"type": "var", "value": tok.value}

        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.match(TokenType.RPAREN)
            return expr

        raise Exception(f"Factor inesperado en {tok}")

    def parse_primary(self):
        tok = self.peek()

        if tok.type == TokenType.NUMBER:
            return {"type": "number", "value": self.advance().value}

        if tok.type == TokenType.IDENT:
            return {"type": "var", "value": self.advance().value}

        raise Exception(f"Expresión no válida comenzando en {tok}")