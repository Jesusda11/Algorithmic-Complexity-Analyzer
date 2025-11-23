"""
Validador Semántico para el Analizador de Pseudocódigo

Garantiza que se cumplan las reglas semánticas del lenguaje:
1. Los objetos deben declararse al principio del algoritmo
2. Los objetos solo pueden acceder a campos definidos en su clase
3. Las variables deben declararse antes de usarse
"""


class SemanticError(Exception):
    """Excepción para errores semánticos"""
    pass


class SemanticValidator:
    def __init__(self, ast):
        self.ast = ast
        self.classes = {}  # {class_name: [attributes]}
        self.declared_objects = {}  # {object_name: class_name}
        self.declared_vars = set()  # {var_name}
        self.declared_arrays = set()  # {array_name}
        
    def validate(self):
        """
        Ejecuta todas las validaciones semánticas
        Retorna True si es válido, lanza SemanticError si no
        """
        # 1. Extraer definiciones de clases
        self._extract_classes()
        
        # 2. Validar que los objetos se declaren al principio
        self._validate_object_declarations_at_beginning()
        
        # 3. Validar acceso a campos
        self._validate_field_access()
        
        # 4. Validar que las variables estén declaradas antes de usarse
        self._validate_variable_usage()
        
        return True
    
    def _extract_classes(self):
        """Extrae todas las definiciones de clases del AST"""
        if "classes" in self.ast:
            for class_def in self.ast["classes"]:
                class_name = class_def["name"]
                attributes = class_def["attributes"]
                self.classes[class_name] = attributes
        
        # Extraer declaraciones de objetos del cuerpo principal también
        self._extract_declarations_from_body(self.ast["body"])

    def _extract_declarations_from_body(self, body):
        """Extrae declaraciones del cuerpo principal del programa"""
        for stmt in body:
            if stmt["type"] == "object_decl":
                obj_name = stmt["name"]
                class_name = stmt["class_name"]
                self.declared_objects[obj_name] = class_name
            elif stmt["type"] == "var_decl":
                self.declared_vars.add(stmt["name"])
            elif stmt["type"] == "array_decl":
                self.declared_arrays.add(stmt["name"])
    
    def _validate_object_declarations_at_beginning(self):
        """
        Valida que todos los objetos se declaren al principio del programa
        y de cada bloque
        """
        # Validar el cuerpo principal del programa
        self._validate_declarations_order_in_body(self.ast["body"])
        
        # Validar todos los bloques anidados
        for block in self._find_all_blocks(self.ast["body"]):
            self._validate_declarations_order_in_block(block)

    def _validate_declarations_order_in_body(self, body):
        """
        Verifica que en el cuerpo principal, todas las declaraciones vengan primero
        """
        declarations_ended = False
        
        for i, stmt in enumerate(body):
            stmt_type = stmt["type"]
            
            # Si es declaración
            if stmt_type in ("var_decl", "array_decl", "object_decl"):
                if declarations_ended:
                    raise SemanticError(
                        f"Error: Las declaraciones deben estar al principio del programa. "
                        f"Encontrada declaración '{stmt}' después de otras operaciones."
                    )
                
                # Registrar la declaración
                if stmt_type == "object_decl":
                    obj_name = stmt["name"]
                    class_name = stmt["class_name"]
                    
                    # Verificar que la clase existe
                    if class_name not in self.classes:
                        raise SemanticError(
                            f"Error: Clase '{class_name}' no está definida. "
                            f"Objeto '{obj_name}' no puede ser declarado."
                        )
                    
                    self.declared_objects[obj_name] = class_name
                
                elif stmt_type == "var_decl":
                    self.declared_vars.add(stmt["name"])
                
                elif stmt_type == "array_decl":
                    self.declared_arrays.add(stmt["name"])
            
            # Si NO es declaración, marcar que las declaraciones terminaron
            else:
                declarations_ended = True

    def _validate_declarations_order_in_block(self, block):
        """
        Verifica que en un bloque, todas las declaraciones vengan primero
        """
        if block["type"] != "block":
            return
        
        declarations_ended = False
        
        for i, stmt in enumerate(block["body"]):
            stmt_type = stmt["type"]
            
            # Si es declaración
            if stmt_type in ("var_decl", "array_decl", "object_decl"):
                if declarations_ended:
                    raise SemanticError(
                        f"Error: Las declaraciones deben estar al principio del bloque. "
                        f"Encontrada declaración '{stmt}' después de otras operaciones."
                    )
                
                # Registrar la declaración
                if stmt_type == "object_decl":
                    obj_name = stmt["name"]
                    class_name = stmt["class_name"]
                    
                    # Verificar que la clase existe
                    if class_name not in self.classes:
                        raise SemanticError(
                            f"Error: Clase '{class_name}' no está definida. "
                            f"Objeto '{obj_name}' no puede ser declarado."
                        )
                    
                    self.declared_objects[obj_name] = class_name
                
                elif stmt_type == "var_decl":
                    self.declared_vars.add(stmt["name"])
                
                elif stmt_type == "array_decl":
                    self.declared_arrays.add(stmt["name"])
            
            # Si NO es declaración, marcar que las declaraciones terminaron
            else:
                declarations_ended = True
    
    def _validate_field_access(self):
        """
        Valida que el acceso a campos sea correcto:
        1. El objeto debe existir
        2. El campo debe estar definido en la clase del objeto
        """
        field_accesses = self._find_all_field_accesses(self.ast["body"])
        
        for field_access in field_accesses:
            obj_name = field_access["object"]["value"]
            field_name = field_access["field"]
            
            # Verificar que el objeto está declarado
            if obj_name not in self.declared_objects:
                raise SemanticError(
                    f"Error: Objeto '{obj_name}' no está declarado. "
                    f"No se puede acceder al campo '{field_name}'."
                )
            
            # Verificar que el campo existe en la clase
            class_name = self.declared_objects[obj_name]
            class_attributes = self.classes[class_name]
            
            if field_name not in class_attributes:
                raise SemanticError(
                    f"Error: La clase '{class_name}' no tiene el atributo '{field_name}'. "
                    f"Atributos válidos: {', '.join(class_attributes)}"
                )
    
    def _validate_variable_usage(self):
        """
        Valida que las variables se usen después de declararse
        (Implementación básica - puede expandirse)
        """
        # Esta validación es más compleja y requiere análisis de flujo
        # Por ahora, solo verificamos en el scope global
        pass
    
    # -----------------------------
    # UTILIDADES DE BÚSQUEDA EN AST
    # -----------------------------
    
    def _find_all_blocks(self, nodes):
        """Encuentra todos los bloques begin...end en el AST"""
        blocks = []
        
        def traverse(node):
            if isinstance(node, dict):
                if node.get("type") == "block":
                    blocks.append(node)
                
                for value in node.values():
                    traverse(value)
            
            elif isinstance(node, list):
                for item in node:
                    traverse(item)
        
        traverse(nodes)
        return blocks
    
    def _find_all_field_accesses(self, nodes):
        """Encuentra todos los accesos a campos de objetos"""
        field_accesses = []
        
        def traverse(node):
            if isinstance(node, dict):
                if node.get("type") == "field_access":
                    field_accesses.append(node)
                
                for value in node.values():
                    traverse(value)
            
            elif isinstance(node, list):
                for item in node:
                    traverse(item)
        
        traverse(nodes)
        return field_accesses
    
    def _validate_variable_usage(self):
        """
        Valida que todas las variables usadas estén declaradas
        """
        used_vars = self._find_all_variable_usage(self.ast["body"])
        
        for var_name in used_vars:
            if (var_name not in self.declared_vars and 
                var_name not in self.declared_objects and
                var_name not in self.declared_arrays):
                raise SemanticError(
                    f"Error: Variable '{var_name}' no está declarada. "

                )

    def _find_all_variable_usage(self, nodes):
        """Encuentra todas las variables usadas en el AST"""
        used_vars = set()
        
        def traverse(node):
            if isinstance(node, dict):
                # Variable en asignación (lado izquierdo)
                if node.get("type") == "var":
                    used_vars.add(node["value"])
                
                # Variable en acceso a campo
                elif node.get("type") == "field_access":
                    if node["object"]["type"] == "var":
                        used_vars.add(node["object"]["value"])
                
                # Variable en acceso a array
                elif node.get("type") == "array_access":
                    if node["array"]["type"] == "var":
                        used_vars.add(node["array"]["value"])
                    if node["index"]["type"] == "var":
                        used_vars.add(node["index"]["value"])
                
                # Recursión
                for value in node.values():
                    traverse(value)
            
            elif isinstance(node, list):
                for item in node:
                    traverse(item)
        
        traverse(nodes)
        return used_vars


# -----------------------------
# EJEMPLO DE USO
# -----------------------------

def validate_pseudocode(ast):
    """
    Función principal para validar el AST
    
    Args:
        ast: AST generado por el parser
    
    Returns:
        True si es válido
    
    Raises:
        SemanticError: Si hay errores semánticos
    """
    validator = SemanticValidator(ast)
    return validator.validate()


# -----------------------------
# TESTS
# -----------------------------

def test_valid_object_declaration():
    """Test: Declaración válida de objetos al principio"""
    ast = {
        "type": "program",
        "classes": [
            {
                "type": "class_def",
                "name": "Casa",
                "attributes": ["Area", "color", "propietario"]
            }
        ],
        "body": [
            {
                "type": "object_decl",
                "class_name": "Casa",
                "name": "miCasa"
            },
            {
                "type": "var_decl",
                "name": "x"
            },
            {
                "type": "assign",
                "target": {
                    "type": "field_access",
                    "object": {"type": "var", "value": "miCasa"},
                    "field": "Area"
                },
                "expr": {"type": "number", "value": 100}
            }
        ]
    }
    
    try:
        validate_pseudocode(ast)
        print("✅ Test 1 PASSED: Declaración válida de objetos")
    except SemanticError as e:
        print(f"❌ Test 1 FAILED: {e}")


def test_invalid_object_declaration_order():
    """Test: Declaración de objeto después de asignación (INVÁLIDO)"""
    ast = {
        "type": "program",
        "classes": [
            {
                "type": "class_def",
                "name": "Casa",
                "attributes": ["Area", "color"]
            }
        ],
        "body": [
            {
                "type": "assign",
                "target": {"type": "var", "value": "x"},
                "expr": {"type": "number", "value": 5}
            },
            {
                "type": "object_decl",  # ❌ Declaración después de asignación
                "class_name": "Casa",
                "name": "miCasa"
            }
        ]
    }
    
    try:
        validate_pseudocode(ast)
        print("❌ Test 2 FAILED: Debería haber detectado error de orden")
    except SemanticError as e:
        print(f"✅ Test 2 PASSED: Error detectado correctamente - {e}")


def test_invalid_field_access():
    """Test: Acceso a campo inexistente"""
    ast = {
        "type": "program",
        "classes": [
            {
                "type": "class_def",
                "name": "Casa",
                "attributes": ["Area", "color"]
            }
        ],
        "body": [
            {
                "type": "object_decl",
                "class_name": "Casa",
                "name": "miCasa"
            },
            {
                "type": "assign",
                "target": {
                    "type": "field_access",
                    "object": {"type": "var", "value": "miCasa"},
                    "field": "altura"  # ❌ Campo no existe
                },
                "expr": {"type": "number", "value": 100}
            }
        ]
    }
    
    try:
        validate_pseudocode(ast)
        print("❌ Test 3 FAILED: Debería haber detectado campo inexistente")
    except SemanticError as e:
        print(f"✅ Test 3 PASSED: Error detectado correctamente - {e}")


def test_undeclared_class():
    """Test: Uso de clase no definida"""
    ast = {
        "type": "program",
        "classes": [],
        "body": [
            {
                "type": "object_decl",
                "class_name": "Edificio",  
                "name": "miEdificio"
            }
        ]
    }
    
    try:
        validate_pseudocode(ast)
        print("❌ Test 4 FAILED: Debería haber detectado clase no definida")
    except SemanticError as e:
        print(f"✅ Test 4 PASSED: Error detectado correctamente - {e}")


if __name__ == "__main__":
    print("=" * 70)
    print("EJECUTANDO TESTS DE VALIDACIÓN SEMÁNTICA")
    print("=" * 70)
    print()
    
    test_valid_object_declaration()
    test_invalid_object_declaration_order()
    test_invalid_field_access()
    test_undeclared_class()
    
    print()
    print("=" * 70)
    print("TESTS COMPLETADOS")
    print("=" * 70)