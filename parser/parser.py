from lexer.token import TokenType


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # -----------------------------
    # UTILIDADES
    # -----------------------------
    def peek(self):
        """Retorna el token actual sin avanzar"""
        return self.tokens[self.pos]

    def advance(self):
        """Avanza al siguiente token y retorna el actual"""
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def match(self, type_):
        """Verifica que el token actual sea del tipo esperado y avanza"""
        if self.peek().type == type_:
            return self.advance()
        raise Exception(f"Se esperaba {type_} y se encontrÃ³ {self.peek()}")

    def optional(self, type_):
        """Si el token actual es del tipo dado, lo consume y retorna; si no, retorna None"""
        if self.peek().type == type_:
            return self.advance()
        return None

    def skip_newlines(self):
        """Salta todos los tokens NEWLINE consecutivos"""
        while self.peek().type == TokenType.NEWLINE:
            self.advance()

    # -----------------------------
    # ENTRYPOINT
    # -----------------------------
    def parse(self):
        """Punto de entrada principal del parser"""
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
        """Parsea un statement genÃ©rico"""
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
            # Lookahead mÃ¡s sofisticado para distinguir casos
            return self.parse_ident_statement()
        if tok.type == TokenType.BEGIN:
            return self.parse_block()

        return None

    def parse_ident_statement(self):
        """
        Distingue entre declaraciÃ³n y asignaciÃ³n basÃ¡ndose en lookahead.

        Casos:
        1. A[10]           â†’ declaraciÃ³n de arreglo
        2. A[n..m]         â†’ declaraciÃ³n de arreglo con rango
        3. i               â†’ declaraciÃ³n de variable simple
        4. i ðŸ¡¨ 0           â†’ asignaciÃ³n
        5. A[i] ðŸ¡¨ 5        â†’ asignaciÃ³n a elemento de arreglo
        6. A[1..j] ðŸ¡¨ B    â†’ asignaciÃ³n a subarreglo
        """
        # Guardar posiciÃ³n para posible backtrack
        saved_pos = self.pos

        ident = self.advance()  # consumir el identificador

        # Si no hay nada mÃ¡s, es una declaraciÃ³n simple
        if self.peek().type in (TokenType.NEWLINE, TokenType.END, TokenType.EOF):
            return {"type": "var_decl", "name": ident.value}

        # Si viene ASSIGN directamente, es asignaciÃ³n simple: i ðŸ¡¨ valor
        if self.peek().type == TokenType.ASSIGN:
            self.pos = saved_pos  # restaurar
            return self.parse_assign()

        # Si viene LBRACKET, necesitamos analizar mÃ¡s
        if self.peek().type == TokenType.LBRACKET:
            self.advance()  # consumir '['

            # Parsear la expresiÃ³n dentro de los corchetes
            expr = self.parse_expression()

            # Verificar quÃ© viene despuÃ©s
            if self.peek().type == TokenType.RANGE:
                # Es declaraciÃ³n con rango: A[n..m]
                self.pos = saved_pos  # restaurar y parsear como declaraciÃ³n
                return self.parse_var_declaration()
            elif self.peek().type == TokenType.RBRACKET:
                self.advance()  # consumir ']'

                # Verificar quÃ© sigue despuÃ©s del ']'
                next_tok = self.peek().type

                if next_tok == TokenType.ASSIGN:
                    # Es asignaciÃ³n: A[i] ðŸ¡¨ valor
                    self.pos = saved_pos
                    return self.parse_assign()
                elif next_tok == TokenType.LBRACKET:
                    # PodrÃ­a ser A[i][j] (asignaciÃ³n multidimensional)
                    # o A[n][m] (declaraciÃ³n multidimensional)
                    # Por ahora asumimos asignaciÃ³n
                    self.pos = saved_pos
                    return self.parse_assign()
                else:
                    # Es declaraciÃ³n: A[10] o A[n]
                    self.pos = saved_pos
                    return self.parse_var_declaration()

        # Caso por defecto: declaraciÃ³n
        self.pos = saved_pos
        return self.parse_var_declaration()

    # -----------------------------
    # ASSIGN
    # -----------------------------
    def parse_assign(self):
        """
        Parsea asignaciones:
        - var ðŸ¡¨ expr
        - A[i] ðŸ¡¨ expr
        - A[i..j] ðŸ¡¨ expr (asignaciÃ³n a un subarreglo)
        """
        ident = self.match(TokenType.IDENT)
        target = self.parse_array_suffix({"type": "var", "value": ident.value})
        self.match(TokenType.ASSIGN)
        expr = self.parse_expression()
        return {"type": "assign", "target": target, "expr": expr}

    # -----------------------------
    # VARIABLE / ARRAY DECLARATION
    # -----------------------------
    def parse_var_declaration(self):
        """
        Parsea declaraciones de variables y arreglos:
        - nombre
        - nombre[tamaÃ±o]
        - nombre[n..m] (declaraciÃ³n con rango)
        - nombre[dim1][dim2]... (arreglos multidimensionales)
        """
        ident = self.match(TokenType.IDENT)
        node = {"type": "var_decl", "name": ident.value}

        # Si tiene corchetes â†’ es un arreglo
        dims = []
        while self.peek().type == TokenType.LBRACKET:
            self.advance()  # consumir '['
            dim_expr = self.parse_expression()

            if self.peek().type == TokenType.RANGE:
                # DeclaraciÃ³n con rango: nombre[n..m]
                self.advance()  # consumir '..'
                end_expr = self.parse_expression()
                dims.append({"type": "range", "start": dim_expr, "end": end_expr})
            else:
                # DeclaraciÃ³n simple: nombre[n]
                dims.append({"type": "size", "value": dim_expr})

            self.match(TokenType.RBRACKET)

        if dims:
            node["type"] = "array_decl"
            node["dims"] = dims

        return node

    # -----------------------------
    # CALL
    # -----------------------------
    def parse_call(self):
        """
        Parsea llamadas a procedimientos:
        CALL nombre(arg1, arg2, ..., argN)
        """
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
        """
        Parsea ciclos FOR:
        for var ðŸ¡¨ inicio to fin do
            begin
                ...
            end
        """
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
        """
        Parsea condicionales IF:
        if (condiciÃ³n) then
            begin ... end
        else
            begin ... end
        """
        self.match(TokenType.IF)
        self.match(TokenType.LPAREN)
        cond = self.parse_expression()
        self.match(TokenType.RPAREN)
        self.match(TokenType.THEN)
        self.skip_newlines()
        then_block = self.parse_block()
        self.skip_newlines()

        # El ELSE es obligatorio segÃºn la gramÃ¡tica del proyecto
        self.match(TokenType.ELSE)
        self.skip_newlines()
        else_block = self.parse_block()

        return {"type": "if", "cond": cond, "then": then_block, "else": else_block}

    # -----------------------------
    # WHILE
    # -----------------------------
    def parse_while(self):
        """
        Parsea ciclos WHILE:
        while (condiciÃ³n) do
            begin ... end
        """
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
        """
        Parsea ciclos REPEAT:
        repeat
            ...
        until (condiciÃ³n)
        """
        self.match(TokenType.REPEAT)
        self.skip_newlines()
        statements = []
        while self.peek().type not in (TokenType.UNTIL, TokenType.EOF):
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        self.match(TokenType.UNTIL)
        self.match(TokenType.LPAREN)
        cond = self.parse_expression()
        self.match(TokenType.RPAREN)
        return {"type": "repeat", "body": statements, "cond": cond}

    # -----------------------------
    # BLOCK
    # -----------------------------
    def parse_block(self):
        """
        Parsea bloques:
        begin
            statement1
            statement2
            ...
        end
        """
        self.skip_newlines()
        self.match(TokenType.BEGIN)
        statements = []
        while self.peek().type not in (TokenType.END, TokenType.EOF):
            self.skip_newlines()
            if self.peek().type == TokenType.END:
                break
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        self.match(TokenType.END)
        return {"type": "block", "body": statements}

    # -----------------------------
    # EXPRESSIONS
    # -----------------------------
    def parse_expression(self):
        """
        Parsea expresiones con operadores relacionales (<, >, =, â‰¤, â‰¥, â‰ )
        """
        node = self.parse_additive()
        if self.peek().type in (TokenType.GT, TokenType.LT, TokenType.EQ,
                                TokenType.LE, TokenType.GE, TokenType.NE):
            op = self.advance()
            right = self.parse_additive()
            return {"type": "binop", "op": op.type, "left": node, "right": right}
        return node

    def parse_additive(self):
        """Parsea expresiones aditivas (+, -)"""
        node = self.parse_term()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance()
            right = self.parse_term()
            node = {"type": "binop", "op": op.type, "left": node, "right": right}
        return node

    def parse_term(self):
        """Parsea tÃ©rminos multiplicativos (*, /, mod, div)"""
        node = self.parse_factor()
        while self.peek().type in (TokenType.MULT, TokenType.DIV,
                                   TokenType.MOD, TokenType.DIV_INT):
            op = self.advance()
            right = self.parse_factor()
            node = {"type": "binop", "op": op.type, "left": node, "right": right}
        return node

    def parse_factor(self):
        """
        Parsea factores:
        - nÃºmeros
        - identificadores (con posible acceso a arreglos)
        - expresiones entre parÃ©ntesis
        """
        tok = self.peek()
        if tok.type == TokenType.NUMBER:
            self.advance()
            return {"type": "number", "value": tok.value}
        if tok.type == TokenType.IDENT:
            ident = self.advance()
            node = {"type": "var", "value": ident.value}
            return self.parse_array_suffix(node)
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.match(TokenType.RPAREN)
            return expr
        raise Exception(f"Factor inesperado en {tok}")

    # -----------------------------
    # ARRAY ACCESS (CLAVE)
    # -----------------------------
    def parse_array_suffix(self, base):
        """
        Parsea sufijos de acceso a arreglos.

        Ejemplos:
        - A[i]           â†’ acceso a un elemento
        - A[1..j]        â†’ acceso a un subarreglo (rango)
        - A[i][j]        â†’ acceso multidimensional
        - A[i..j][k]     â†’ combinaciÃ³n de rango y acceso

        Retorna un AST con la estructura adecuada:
        - array_access: para A[i]
        - array_range: para A[1..j]
        """
        while self.optional(TokenType.LBRACKET):
            start = self.parse_expression()

            # Verificar si es un rango (notaciÃ³n ..)
            if self.optional(TokenType.RANGE):
                # A[inicio..fin] â†’ subarreglo
                end = self.parse_expression()
                self.match(TokenType.RBRACKET)
                base = {
                    "type": "array_range",
                    "array": base,
                    "start": start,
                    "end": end
                }
            else:
                # A[Ã­ndice] â†’ acceso a elemento
                self.match(TokenType.RBRACKET)
                base = {
                    "type": "array_access",
                    "array": base,
                    "index": start
                }

        return base

