def parse_var_declaration(self):
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

        # MEJORAR EL MENSAJE DE ERROR:
        current = self.peek()
        raise Exception(
            f"Se esperaba {type_}, "
            f"pero se encontró {current.type} = '{current.value}' "
            f"en línea {current.line}, columna {current.col}"
        )

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
        classes = []
        procedures = []
        graphs = []
        statements = []

        while self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.EOF:
                break

            # NUEVO: Detectar declaración de grafo
            if self.peek().type == TokenType.GRAFO:
                graphs.append(self.parse_graph_declaration())
                self.skip_newlines()
                continue

            # Clase: IDENT + LBRACE
            if (self.peek().type == TokenType.IDENT and
                    self.pos + 1 < len(self.tokens) and
                    self.tokens[self.pos + 1].type == TokenType.LBRACE):
                classes.append(self.parse_class_definition())
                self.skip_newlines()
            else:
                break

        while self.peek().type == TokenType.PROCEDURE:
            self.skip_newlines()
            procedures.append(self.parse_procedure_declaration())
            self.skip_newlines()

        while self.peek().type != TokenType.EOF:
            self.skip_newlines()
            if self.peek().type == TokenType.EOF:
                break

            stmt = self.statement()
            if stmt:
                statements.append(stmt)

            self.skip_newlines()

        return {
            "type": "program",
            "classes": classes,
            "procedures": procedures,
            "graphs": graphs,  # NUEVO: incluir grafos en el AST
            "body": statements
        }
    # -----------------------------
    # CLASES
    # -----------------------------

    def parse_class_definition(self):
        class_name = self.match(TokenType.IDENT)
        self.match(TokenType.LBRACE)
        attributes = []

        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()

            if self.peek().type == TokenType.IDENT:
                attr = self.match(TokenType.IDENT)
                attributes.append(attr.value)
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
    # PROCEDURES
    # -----------------------------

    def parse_procedure_declaration(self):
        self.match(TokenType.PROCEDURE)
        name = self.match(TokenType.IDENT)
        self.match(TokenType.LPAREN)

        params = []
        if self.peek().type != TokenType.RPAREN:
            params.append(self.parse_parameter())
            while self.optional(TokenType.COMMA):
                params.append(self.parse_parameter())

        self.match(TokenType.RPAREN)
        self.skip_newlines()

        body = self.parse_block()

        return {
            "type": "procedure_decl",
            "name": name.value,
            "params": params,
            "body": body
        }

    def parse_parameter(self):
        if (self.peek().type == TokenType.IDENT and
                self.peek().value[0].isupper()):

            if (self.pos + 1 < len(self.tokens) and
                    self.tokens[self.pos + 1].type == TokenType.IDENT and
                    self.tokens[self.pos + 1].value[0].islower()):
                class_name = self.match(TokenType.IDENT)
                param_name = self.match(TokenType.IDENT)

                return {
                    "type": "object_param",
                    "class_name": class_name.value,
                    "name": param_name.value
                }

        param_name_tok = self.match(TokenType.IDENT)
        param_name = param_name_tok.value

        dims = []
        while self.peek().type == TokenType.LBRACKET:
            self.advance()
            if self.peek().type == TokenType.RBRACKET:
                dims.append({"type": "unspecified"})
            elif self.peek().type == TokenType.RANGE:
                self.advance()
                dims.append({"type": "range_unspecified"})
            else:
                start_expr = self.parse_expression()
                if self.optional(TokenType.RANGE):
                    end_expr = self.parse_expression()
                    dims.append({
                        "type": "range",
                        "start": start_expr,
                        "end": end_expr
                    })
                else:
                    dims.append({"type": "size", "value": start_expr})

            self.match(TokenType.RBRACKET)

        if dims:
            return {"type": "array_param", "name": param_name, "dims": dims}
        else:
            return {"type": "primitive_param", "name": param_name}
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
        if tok.type == TokenType.RETURN:
            return self.parse_return()
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
        saved_pos = self.pos
        ident = self.advance()

        if (ident.value[0].isupper() and
                self.peek().type == TokenType.IDENT and
                self.peek().value[0].islower()):
            self.pos = saved_pos
            return self.parse_object_declaration()

        if self.peek().type in (TokenType.NEWLINE, TokenType.END, TokenType.EOF):
            return {"type": "var_decl", "name": ident.value}

        if self.peek().type == TokenType.ASSIGN:
            self.pos = saved_pos
            return self.parse_assign()

        if self.peek().type == TokenType.DOT:
            self.pos = saved_pos
            return self.parse_assign()

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

        self.pos = saved_pos
        return self.parse_var_declaration()
    # -----------------------------
    # OBJETOS
    # -----------------------------

    def parse_object_declaration(self):
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
        start_token = self.peek()
        ident = self.match(TokenType.IDENT)
        target = {"type": "var", "value": ident.value}

        if self.peek().type == TokenType.DOT:
            self.advance()
            field = self.match(TokenType.IDENT)
            target = {
                "type": "field_access",
                "object": target,
                "field": field.value
            }
        else:
            target = self.parse_array_suffix(target)

        self.match(TokenType.ASSIGN)
        expr = self.parse_expression()
        return {"type": "assign", "target": target, "expr": expr, "line": start_token.line, "col": start_token.col}
    # -----------------------------
    # VAR / ARRAY DECLARATION

    def parse_var_declaration(self):
        
        start_token = self.peek()

        ident = self.match(TokenType.IDENT)
        node = {"type": "var_decl", "name": ident.value, "line": start_token.line, "col": start_token.col}

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
            node["line"] = start_token.line # Mantenemos la línea
            node["col"] = start_token.col   # Mantenemos la columna

        return node
    # -----------------------------
    # CALL
    # -----------------------------
    def parse_call(self):
        self.match(TokenType.CALL)
        proc_name = self.match(TokenType.IDENT)
        self.match(TokenType.LPAREN)

        args = []
        if self.peek().type != TokenType.RPAREN:
            args.append(self.parse_expression())
            while self.optional(TokenType.COMMA):
                args.append(self.parse_expression())

        self.match(TokenType.RPAREN)

        return {
            "type": "call",
            "name": proc_name.value,
            "args": args
        }
    # -----------------------------

    # -----------------------------
    # FOR
    # -----------------------------
    def parse_for(self):

        for_token = self.match(TokenType.FOR)

        var = self.match(TokenType.IDENT)
        self.match(TokenType.ASSIGN)
        start = self.parse_expression()
        self.match(TokenType.TO)
        end = self.parse_expression()
        self.match(TokenType.DO)
        self.skip_newlines()
        body = self.parse_block()
        return {
            "type": "for",
            "var": var.value,
            "start": start,
            "end": end,
            "body": body,
            "line": for_token.line,  # <-- ¡Añadir!
            "col": for_token.col
        }

    # -----------------------------
    # IF
    # -----------------------------
    def parse_if(self):

        if_token = self.match(TokenType.IF)

        self.match(TokenType.LPAREN)
        cond = self.parse_expression()
        self.match(TokenType.RPAREN)
        self.match(TokenType.THEN)

        self.skip_newlines()
        then_block = self.parse_block()
        self.skip_newlines()

        # -------------------------
        # ELSE opcional
        # -------------------------
        else_block = None
        if self.peek().type == TokenType.ELSE:
            self.advance()  # consumir ELSE
            self.skip_newlines()
            else_block = self.parse_block()

        return {
            "type": "if",
            "cond": cond,
            "then": then_block,
            "else": else_block,
            "line": if_token.line,  # <-- ¡Añadir!
            "col": if_token.col
        }

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
    # EXPRESSIONS (BOOLEAN + SHORT-CIRCUIT READY)
    # -----------------------------
    def parse_expression(self):
        """Nivel más alto: OR"""
        node = self.parse_and()

        while self.peek().type == TokenType.OR:
            op = self.advance()
            right = self.parse_and()
            node = {"type": "binop", "op": op.type, "left": node, "right": right}

        return node

    def parse_and(self):
        """Nivel AND"""
        node = self.parse_relational()

        while self.peek().type == TokenType.AND:
            op = self.advance()
            right = self.parse_relational()
            node = {"type": "binop", "op": op.type, "left": node, "right": right}

        return node

    def parse_relational(self):
        """= ≠ < > <= >="""
        node = self.parse_additive()

        if self.peek().type in (
            TokenType.GT, TokenType.LT, TokenType.EQ,
            TokenType.LE, TokenType.GE, TokenType.NE
        ):
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

        # 👈 CAMBIO 1: NUEVA REGLA para Array Literal: [1, 2, 3]
        if tok.type == TokenType.LBRACKET:
            # Si encontramos '[', llamamos a la función de parsing de array
            return self.parse_array_literal()
        
        if tok.type == TokenType.MINUS:
            self.advance()  # Consumir el '-'
            
            # Verificar que lo siguiente sea un número
            if self.peek().type == TokenType.NUMBER:
                num_tok = self.advance()
                return {"type": "number", "value": -num_tok.value}
            else:
                # Es una expresión negativa: -(expr)
                factor = self.parse_factor()
                return {
                    "type": "unary",
                    "op": "MINUS",
                    "operand": factor
                }

        if tok.type == TokenType.NOT:
            self.advance()
            expr = self.parse_factor()
            return {"type": "unaryop", "op": TokenType.NOT, "expr": expr}

        if tok.type == TokenType.NUMBER:
            self.advance()
            return {"type": "number", "value": tok.value}

        if tok.type == TokenType.STRING:
            self.advance()
            return {"type": "string", "value": tok.value}

        if tok.type == TokenType.TRUE:
            self.advance()
            return {"type": "boolean", "value": True}

        if tok.type == TokenType.FALSE:
            self.advance()
            return {"type": "boolean", "value": False}

        if tok.type == TokenType.NULL:
            self.advance()
            return {"type": "null", "value": None}

        if tok.type in (
            TokenType.LENGTH, TokenType.UPPER, TokenType.LOWER,
            TokenType.SUBSTRING, TokenType.TRIM
        ):
            func = self.advance()
            self.match(TokenType.LPAREN)
            args = [self.parse_expression()]
            while self.optional(TokenType.COMMA):
                args.append(self.parse_expression())
            self.match(TokenType.RPAREN)

            return {"type": "string_func", "func": func.type.lower(), "args": args}

        if tok.type == TokenType.IDENT:
            ident = self.advance()

            if ident.value == "T":
                return {"type": "boolean", "value": True}
            if ident.value == "F":
                return {"type": "boolean", "value": False}

            node = {"type": "var", "value": ident.value}

            if self.peek().type == TokenType.DOT:
                self.advance()
                field = self.match(TokenType.IDENT)
                node = {
                    "type": "field_access",
                    "object": node,
                    "field": field.value
                }

            return self.parse_array_suffix(node)
        
        if tok.type == TokenType.CALL:
            return self.parse_call_expression()

        if tok.type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.match(TokenType.RPAREN)
            return expr

        # ┌ x ┐  (techo)
        if tok.type == TokenType.CEIL:
            self.advance()
            expr = self.parse_expression()
            self.match(TokenType.CEIL_END)
            return {"type": "ceil", "expr": expr}

        # └ x ┘  (piso)
        if tok.type == TokenType.FLOOR:
            self.advance()
            expr = self.parse_expression()
            self.match(TokenType.FLOOR_END)
            return {"type": "floor", "expr": expr}


        raise Exception(f"Factor inesperado: {tok.type} = '{tok.value}' en línea {tok.line}, columna {tok.col}")

    # -----------------------------
    # ARRAY ACCESS
    # -----------------------------

    def parse_array_literal(self):
        """
        Parsea un literal de array: [expr, expr, ...]
        Ejemplo: [1, 2+3, CALL Suma(x)]
        """
        # Aseguramos que el token actual es '['
        self.match(TokenType.LBRACKET) 
        
        elements = []
        
        # Verificar si no es un array vacío '[]'
        if self.peek().type != TokenType.RBRACKET:
            # Parsear el primer elemento
            elements.append(self.parse_expression())
            
            # Parsear los elementos subsiguientes separados por coma
            while self.optional(TokenType.COMMA):
                elements.append(self.parse_expression())
        
        # Aseguramos que el token actual es ']'
        self.match(TokenType.RBRACKET) 
        
        # Devolver un nuevo nodo AST
        return {
            "type": "array_literal",
            "elements": elements,
            "line": self.tokens[self.pos - 1].line, # O la línea del '['
            "col": self.tokens[self.pos - 1].col
        }
    
    # src/parser.py (Dentro de la clase Parser)

    def parse_primary_expression(self):
        # 1. 👈 NUEVA REGLA: Verificar si es un literal de array [1, 2, 3]
        if self.peek().type == TokenType.LBRACKET:
            return self.parse_array_literal()

        # 2. Manejo de números, booleanos, null, etc.
        if self.peek().type in (TokenType.NUMBER, TokenType.STRING, TokenType.TRUE, TokenType.FALSE, TokenType.NULL):
            tok = self.advance()
            return {"type": tok.type.name.lower(), "value": tok.value, "line": tok.line, "col": tok.col}

        # 3. Manejo de expresiones entre paréntesis
        if self.optional(TokenType.LPAREN):
            expr = self.parse_expression()
            self.match(TokenType.RPAREN)
            return expr
            
        # 4. Manejo de variables y llamadas a funciones/arrays
        if self.peek().type == TokenType.IDENT:
            node = self.parse_variable_access() # Maneja A, A[i], A[i][j]
            return node
            
        # 5. Manejo de CALL como expresión
        if self.peek().type == TokenType.CALL:
            return self.parse_call_expression()
            
        # ... Resto de tu lógica ...
        
        # Si no se encuentra ninguna expresión primaria esperada
        raise Exception(f"Expresión primaria inesperada en línea {self.peek().line}")
    
    def parse_array_suffix(self, base):
        while self.optional(TokenType.LBRACKET):
            start = self.parse_expression()
            if self.optional(TokenType.RANGE):
                end = self.parse_expression()
                self.match(TokenType.RBRACKET)
                base = {
                    "type": "array_range",
                    "array": base,
                    "start": start,
                    "end": end
                }
            else:
                self.match(TokenType.RBRACKET)
                base = {
                    "type": "array_access",
                    "array": base,
                    "index": start
                }

        return base

    def parse_graph_declaration(self):
        """
        Sintaxis:
        grafo nombreGrafo {
            nodos 🡨 5
            aristas 🡨 [[0,1], [1,2]]
            pesos 🡨 [10, 20]
            dirigido 🡨 T
        }
        """
        self.match(TokenType.GRAFO)
        graph_name = self.match(TokenType.IDENT)
        self.match(TokenType.LBRACE)
        self.skip_newlines()

        properties = {
            "nodos": None,
            "aristas": [],
            "pesos": [],
            "dirigido": False
        }

        while self.peek().type != TokenType.RBRACE and self.peek().type != TokenType.EOF:
            self.skip_newlines()

            if self.peek().type == TokenType.RBRACE:
                break

            prop_name = self.peek()

            # nodos 🡨 N
            if prop_name.type == TokenType.NODOS:
                self.advance()
                self.match(TokenType.ASSIGN)  # SOLO 🡨
                properties["nodos"] = self.parse_expression()

            # aristas 🡨 [[0,1], [1,2]]
            elif prop_name.type == TokenType.ARISTAS:
                self.advance()
                self.match(TokenType.ASSIGN)  # SOLO 🡨
                properties["aristas"] = self.parse_edge_list()

            # pesos 🡨 [10, 20]
            elif prop_name.type == TokenType.PESOS:
                self.advance()
                self.match(TokenType.ASSIGN)  # SOLO 🡨
                properties["pesos"] = self.parse_weight_list()

            # dirigido 🡨 T o F
            elif prop_name.type == TokenType.DIRIGIDO:
                self.advance()
                self.match(TokenType.ASSIGN)  # SOLO 🡨
                dir_expr = self.parse_expression()
                if dir_expr["type"] == "boolean":
                    properties["dirigido"] = dir_expr["value"]

            else:
                # Saltar tokens desconocidos
                self.advance()

            self.skip_newlines()

        self.match(TokenType.RBRACE)

        return {
            "type": "graph_decl",
            "name": graph_name.value,
            "nodos": properties["nodos"],
            "aristas": properties["aristas"],
            "pesos": properties["pesos"],
            "dirigido": properties["dirigido"]
        }

    def parse_edge_list(self):
        """Parsear: [[0,1], [1,2], [2,3]]"""
        self.match(TokenType.LBRACKET)
        edges = []

        while self.peek().type != TokenType.RBRACKET and self.peek().type != TokenType.EOF:
            self.skip_newlines()

            if self.peek().type == TokenType.RBRACKET:
                break

            # Cada arista: [origen, destino]
            self.match(TokenType.LBRACKET)
            origin = self.parse_expression()
            self.match(TokenType.COMMA)
            dest = self.parse_expression()
            self.match(TokenType.RBRACKET)

            edges.append({
                "origin": origin,
                "dest": dest
            })

            # Coma opcional entre aristas
            if self.peek().type == TokenType.COMMA:
                self.advance()

            self.skip_newlines()

        self.match(TokenType.RBRACKET)
        return edges

    def parse_weight_list(self):
        """Parsear: [10, 20, 30]"""
        self.match(TokenType.LBRACKET)
        weights = []

        while self.peek().type != TokenType.RBRACKET and self.peek().type != TokenType.EOF:
            self.skip_newlines()

            if self.peek().type == TokenType.RBRACKET:
                break

            weight = self.parse_expression()
            weights.append(weight)

            if self.peek().type == TokenType.COMMA:
                self.advance()

            self.skip_newlines()

        self.match(TokenType.RBRACKET)
        return weights
    
    def parse_call_expression(self):
        """
        Parsea CALL como expresión (para usar en return, asignaciones, operaciones)
        Ejemplo: return call Fibonacci(n-1)
                x 🡨 call Suma(a, b)
        """
        self.match(TokenType.CALL)
        proc_name = self.match(TokenType.IDENT)
        self.match(TokenType.LPAREN)

        args = []
        if self.peek().type != TokenType.RPAREN:
            args.append(self.parse_expression())
            while self.optional(TokenType.COMMA):
                args.append(self.parse_expression())

        self.match(TokenType.RPAREN)

        return {
            "type": "call_expr",  # Diferente de "call" para distinguir statement vs expresión
            "name": proc_name.value,
            "args": args
        }
    
    def parse_return(self):
        """Parsea: return [expr]"""
        self.match(TokenType.RETURN)
        
        # Puede ser: return solo, o return expr
        if self.peek().type in (TokenType.NEWLINE, TokenType.END, TokenType.EOF):
            return {"type": "return", "expr": None}
        
        # Parsear la expresión (puede incluir CALL)
        expr = self.parse_expression()
        return {"type": "return", "expr": expr}