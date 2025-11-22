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
        raise Exception(f"Se esperaba {type_} y se encontró {self.peek()}")

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
        """
        Punto de entrada principal del parser.
        Primero parsea las definiciones de clases, luego los statements.
        """
        classes = []
        statements = []

        # Paso 1: Parsear definiciones de clases (deben estar antes del algoritmo)
        while self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.EOF:
                break
            
            # Detectar si es una clase: IDENT seguido de LBRACE
            if (self.peek().type == TokenType.IDENT and 
                self.pos + 1 < len(self.tokens) and 
                self.tokens[self.pos + 1].type == TokenType.LBRACE):
                classes.append(self.parse_class_definition())
                self.skip_newlines()
            else:
                # Ya terminaron las clases, salir del loop
                break
        
        # Paso 2: Parsear los statements del algoritmo
        while self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.EOF:
                break

            stmt = self.statement()
            if stmt:
                statements.append(stmt)

            self.skip_newlines()

        return {"type": "program", "classes": classes, "body": statements}

    # -----------------------------
    # DEFINICIÓN DE CLASES
    # -----------------------------
    def parse_class_definition(self):
        """
        Parsea definición de clase:
        Casa {Area color propietario}
        """
        class_name = self.match(TokenType.IDENT)
        self.match(TokenType.LBRACE)
        
        attributes = []
        
        # Leer atributos hasta encontrar }
        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()
            
            if self.peek().type == TokenType.IDENT:
                attr = self.match(TokenType.IDENT)
                attributes.append(attr.value)
            elif self.peek().type == TokenType.RBRACE:
                break
            else:
                if self.peek().type != TokenType.NEWLINE:
                    self.advance()
        
        self.match(TokenType.RBRACE)
        
        return {
            "type": "class_def",
            "name": class_name.value,
            "attributes": attributes
        }

    # -----------------------------
    # STATEMENTS
    # -----------------------------
    def statement(self):
        """Parsea un statement genérico"""
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
            return self.parse_ident_statement()
        if tok.type == TokenType.BEGIN:
            return self.parse_block()

        return None

    def parse_ident_statement(self):
        """
        Distingue entre declaración y asignación basándose en lookahead.
        """
        saved_pos = self.pos
        ident = self.advance()

        # Caso especial: declaración de objeto (Clase nombre_objeto)
        if (ident.value[0].isupper() and 
            self.peek().type == TokenType.IDENT and
            self.peek().value[0].islower()):
            self.pos = saved_pos
            return self.parse_object_declaration()

        # Si no hay nada más, es una declaración simple
        if self.peek().type in (TokenType.NEWLINE, TokenType.END, TokenType.EOF):
            return {"type": "var_decl", "name": ident.value}

        # Si viene ASSIGN directamente, es asignación simple: i 🡨 valor
        if self.peek().type == TokenType.ASSIGN:
            self.pos = saved_pos
            return self.parse_assign()

        # Si viene DOT, es acceso a campo de objeto: miCasa.Area
        if self.peek().type == TokenType.DOT:
            self.pos = saved_pos
            return self.parse_assign()

        # Si viene LBRACKET, necesitamos analizar más
        if self.peek().type == TokenType.LBRACKET:
            self.advance()
            expr = self.parse_expression()

            if self.peek().type == TokenType.RANGE:
                self.pos = saved_pos
                return self.parse_var_declaration()
            elif self.peek().type == TokenType.RBRACKET:
                self.advance()
                next_tok = self.peek().type

                if next_tok == TokenType.ASSIGN:
                    self.pos = saved_pos
                    return self.parse_assign()
                elif next_tok == TokenType.LBRACKET:
                    self.pos = saved_pos
                    return self.parse_assign()
                else:
                    self.pos = saved_pos
                    return self.parse_var_declaration()

        # Caso por defecto: declaración
        self.pos = saved_pos
        return self.parse_var_declaration()

    # -----------------------------
    # DECLARACIÓN DE OBJETOS
    # -----------------------------
    def parse_object_declaration(self):
        """
        Parsea declaración de objetos:
        Casa miCasa
        """
        class_name = self.match(TokenType.IDENT)
        obj_name = self.match(TokenType.IDENT)
        
        return {
            "type": "object_decl",
            "class_name": class_name.value,
            "name": obj_name.value
        }

    # -----------------------------
    # ASSIGN
    # -----------------------------
    def parse_assign(self):
        """
        Parsea asignaciones:
        - var 🡨 expr
        - A[i] 🡨 expr
        - obj.field 🡨 expr
        """
        ident = self.match(TokenType.IDENT)
        target = {"type": "var", "value": ident.value}
        
        # Verificar si es acceso a campo: obj.field
        if self.peek().type == TokenType.DOT:
            self.advance()
            field = self.match(TokenType.IDENT)
            target = {
                "type": "field_access",
                "object": target,
                "field": field.value
            }
        else:
            # Verificar si es acceso a arreglo
            target = self.parse_array_suffix(target)
        
        self.match(TokenType.ASSIGN)
        expr = self.parse_expression()
        return {"type": "assign", "target": target, "expr": expr}

    # -----------------------------
    # VARIABLE / ARRAY DECLARATION
    # -----------------------------
    def parse_var_declaration(self):
        """
        Parsea declaraciones de variables y arreglos
        """
        ident = self.match(TokenType.IDENT)
        node = {"type": "var_decl", "name": ident.value}

        dims = []
        while self.peek().type == TokenType.LBRACKET:
            self.advance()
            dim_expr = self.parse_expression()
            
            if self.peek().type == TokenType.RANGE:
                self.advance()
                end_expr = self.parse_expression()
                dims.append({"type": "range", "start": dim_expr, "end": end_expr})
            else:
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
        """Parsea llamadas a procedimientos"""
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
        """Parsea ciclos FOR"""
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
        """Parsea condicionales IF"""
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
        """Parsea ciclos WHILE"""
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
        """Parsea ciclos REPEAT"""
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
        """Parsea bloques begin...end"""
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
        """Parsea expresiones con operadores relacionales"""
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
        """Parsea términos multiplicativos (*, /, mod, div)"""
        node = self.parse_factor()
        while self.peek().type in (TokenType.MULT, TokenType.DIV,
                                   TokenType.MOD, TokenType.DIV_INT):
            op = self.advance()
            right = self.parse_factor()
            node = {"type": "binop", "op": op.type, "left": node, "right": right}
        return node

    def parse_factor(self):
        """Parsea factores (números, strings, variables, funciones)"""
        tok = self.peek()
        
        # Números
        if tok.type == TokenType.NUMBER:
            self.advance()
            return {"type": "number", "value": tok.value}

        # Strings
        if tok.type == TokenType.STRING:
            self.advance()
            return {"type": "string", "value": tok.value}

        # Booleanos
        if tok.type == TokenType.TRUE:
            self.advance()
            return {"type": "boolean", "value": True}
        
        if tok.type == TokenType.FALSE:
            self.advance()
            return {"type": "boolean", "value": False}

        # NULL
        if tok.type == TokenType.NULL:
            self.advance()
            return {"type": "null", "value": None}

        # Funciones de string: length, upper, lower, substring, trim
        if tok.type in (TokenType.LENGTH, TokenType.UPPER, TokenType.LOWER, 
                       TokenType.SUBSTRING, TokenType.TRIM):
            func = self.advance()
            self.match(TokenType.LPAREN)
            args = [self.parse_expression()]
            while self.optional(TokenType.COMMA):
                args.append(self.parse_expression())
            self.match(TokenType.RPAREN)
            return {"type": "string_func", "func": func.type.lower(), "args": args}

        # Identificadores
        if tok.type == TokenType.IDENT:
            ident = self.advance()
            node = {"type": "var", "value": ident.value}
            
            # Verificar si es acceso a campo: obj.field
            if self.peek().type == TokenType.DOT:
                self.advance()
                field = self.match(TokenType.IDENT)
                node = {
                    "type": "field_access",
                    "object": node,
                    "field": field.value
                }
            
            # Luego verificar acceso a arreglo
            return self.parse_array_suffix(node)

        # Expresiones entre paréntesis
        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.match(TokenType.RPAREN)
            return expr

        raise Exception(f"Factor inesperado en {tok}")

    # -----------------------------
    # ARRAY ACCESS
    # -----------------------------
    def parse_array_suffix(self, base):
        """Parsea sufijos de acceso a arreglos: A[i] o A[1..j]"""
        while self.optional(TokenType.LBRACKET):
            start = self.parse_expression()
            
            if self.optional(TokenType.RANGE):
                end = self.parse_expression()
                self.match(TokenType.RBRACKET)
                base = {"type": "array_range", "array": base, "start": start, "end": end}
            else:
                self.match(TokenType.RBRACKET)
                base = {"type": "array_access", "array": base, "index": start}
        
        return base