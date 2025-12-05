# app/utils/exceptions.py
"""
Excepciones personalizadas del sistema
Cada excepción representa un tipo específico de error en el pipeline
"""
from typing import Optional, Dict, Any


class BaseAPIException(Exception):
    """
    Excepción base para todas las excepciones de la API
    
    Attributes:
        message: Mensaje descriptivo del error
        details: Información adicional del error (línea, columna, etc.)
        error_code: Código único del error para facilitar debugging
    """
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details or {}
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la excepción a diccionario para respuesta JSON"""
        return {
            "error_type": self.error_code,
            "message": self.message,
            "details": self.details
        }


# =============================================
# LEXER ERRORS - Errores de Tokenización
# =============================================

class LexerError(BaseAPIException):
    """
    Error en el análisis léxico (tokenización)
    
    Ocurre cuando:
    - Se encuentra un caracter no válido
    - Un token está mal formado (strings sin cerrar, números mal escritos)
    - Secuencias de caracteres no reconocidas
    
    Ejemplo:
        >>> raise LexerError(
        ...     message="Caracter inesperado '@'",
        ...     details={"line": 5, "column": 12, "char": "@"}
        ... )
    """
    
    def __init__(
        self, 
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
        char: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        
        # Agregar información de ubicación si está disponible
        if line is not None:
            details["line"] = line
        if column is not None:
            details["column"] = column
        if char is not None:
            details["character"] = char
        
        super().__init__(
            message=message,
            details=details,
            error_code="LEXER_ERROR"
        )


class InvalidCharacterError(LexerError):
    """Error específico: caracter no válido en el pseudocódigo"""
    
    def __init__(self, char: str, line: int, column: int):
        super().__init__(
            message=f"Caracter inválido '{char}' en línea {line}, columna {column}",
            line=line,
            column=column,
            char=char
        )


class UnterminatedStringError(LexerError):
    """Error específico: string sin cerrar"""
    
    def __init__(self, line: int):
        super().__init__(
            message=f"String sin cerrar en línea {line}",
            line=line
        )


class InvalidNumberError(LexerError):
    """Error específico: número mal formado"""
    
    def __init__(self, value: str, line: int):
        super().__init__(
            message=f"Número inválido '{value}' en línea {line}",
            line=line,
            details={"value": value}
        )


# =============================================
# PARSER ERRORS - Errores Sintácticos
# =============================================

class ParserError(BaseAPIException):
    """
    Error en el análisis sintáctico (parsing)
    
    Ocurre cuando:
    - Estructura gramatical incorrecta
    - Tokens esperados no encontrados (falta 'end', 'then', etc.)
    - Orden incorrecto de instrucciones
    - Paréntesis/llaves desbalanceadas
    
    Ejemplo:
        >>> raise ParserError(
        ...     message="Se esperaba 'END' pero se encontró 'IF'",
        ...     expected="END",
        ...     found="IF",
        ...     line=10
        ... )
    """
    
    def __init__(
        self,
        message: str,
        expected: Optional[str] = None,
        found: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        if details is None:
            details = {}
        
        if expected is not None:
            details["expected"] = expected
        if found is not None:
            details["found"] = found
        if line is not None:
            details["line"] = line
        if column is not None:
            details["column"] = column
        
        super().__init__(
            message=message,
            details=details,
            error_code="PARSER_ERROR"
        )


class UnexpectedTokenError(ParserError):
    """Error específico: token inesperado"""
    
    def __init__(self, expected: str, found: str, line: int, column: int):
        super().__init__(
            message=f"Se esperaba '{expected}' pero se encontró '{found}' en línea {line}",
            expected=expected,
            found=found,
            line=line,
            column=column
        )


class MissingTokenError(ParserError):
    """Error específico: falta un token requerido"""
    
    def __init__(self, token: str, line: int):
        super().__init__(
            message=f"Falta '{token}' en línea {line}",
            expected=token,
            line=line
        )


class UnbalancedBlockError(ParserError):
    """Error específico: bloques desbalanceados (BEGIN/END)"""
    
    def __init__(self, block_type: str = "BEGIN/END"):
        super().__init__(
            message=f"Bloques {block_type} desbalanceados",
            details={"block_type": block_type}
        )


class InvalidSyntaxError(ParserError):
    """Error específico: sintaxis inválida en una construcción"""
    
    def __init__(self, construction: str, line: int, reason: str):
        super().__init__(
            message=f"Sintaxis inválida en {construction} (línea {line}): {reason}",
            line=line,
            details={"construction": construction, "reason": reason}
        )


# =============================================
# ANALYSIS ERRORS - Errores Semánticos/Análisis
# =============================================

class AnalysisError(BaseAPIException):
    """
    Error en el análisis de complejidad
    
    Ocurre cuando:
    - No se puede determinar la complejidad
    - Variables no definidas o mal usadas
    - Recursión infinita detectada
    - Procedimientos no encontrados
    - Timeout del análisis
    - Estructuras no soportadas
    
    Ejemplo:
        >>> raise AnalysisError(
        ...     message="Variable 'x' usada sin definir",
        ...     variable="x",
        ...     line=8
        ... )
    """
    
    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        super().__init__(
            message=message,
            details=details,
            error_code=error_code or "ANALYSIS_ERROR"
        )


class UndefinedVariableError(AnalysisError):
    """Error específico: variable no definida"""
    
    def __init__(self, variable: str, line: int):
        super().__init__(
            message=f"Variable '{variable}' usada sin definir en línea {line}",
            details={"variable": variable, "line": line},
            error_code="UNDEFINED_VARIABLE"
        )


class UndefinedProcedureError(AnalysisError):
    """Error específico: procedimiento no definido"""
    
    def __init__(self, procedure: str, line: int):
        super().__init__(
            message=f"Procedimiento '{procedure}' no definido (llamado en línea {line})",
            details={"procedure": procedure, "line": line},
            error_code="UNDEFINED_PROCEDURE"
        )


class InfiniteRecursionError(AnalysisError):
    """Error específico: recursión infinita detectada"""
    
    def __init__(self, procedure: str):
        super().__init__(
            message=f"Recursión infinita detectada en '{procedure}' (sin caso base)",
            details={"procedure": procedure},
            error_code="INFINITE_RECURSION"
        )


class ComplexityUndeterminableError(AnalysisError):
    """Error específico: no se puede determinar la complejidad"""
    
    def __init__(self, reason: str):
        super().__init__(
            message=f"No se pudo determinar la complejidad: {reason}",
            details={"reason": reason},
            error_code="COMPLEXITY_UNDETERMINABLE"
        )


class UnsupportedConstructError(AnalysisError):
    """Error específico: construcción no soportada"""
    
    def __init__(self, construct: str, line: int):
        super().__init__(
            message=f"Construcción '{construct}' no soportada en línea {line}",
            details={"construct": construct, "line": line},
            error_code="UNSUPPORTED_CONSTRUCT"
        )


class AnalysisTimeoutError(AnalysisError):
    """Error específico: el análisis excedió el tiempo límite"""
    
    def __init__(self, timeout_seconds: int):
        super().__init__(
            message=f"Análisis excedió el tiempo límite ({timeout_seconds} segundos)",
            details={"timeout_seconds": timeout_seconds},
            error_code="ANALYSIS_TIMEOUT"
        )


# =============================================
# VALIDATION ERRORS - Errores de Validación
# =============================================

class ValidationError(BaseAPIException):
    """
    Error de validación de entrada
    
    Ocurre cuando:
    - Código vacío
    - Código demasiado largo
    - Formato de archivo incorrecto
    - Parámetros inválidos
    """
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            details=details,
            error_code="VALIDATION_ERROR"
        )


class EmptyCodeError(ValidationError):
    """Error específico: código vacío"""
    
    def __init__(self):
        super().__init__(
            message="El código no puede estar vacío",
            field="code"
        )


class CodeTooLargeError(ValidationError):
    """Error específico: código demasiado grande"""
    
    def __init__(self, size: int, max_size: int):
        super().__init__(
            message=f"El código es demasiado grande ({size} bytes). Máximo: {max_size} bytes",
            field="code"
        )


# =============================================
# HELPERS
# =============================================

def format_error_location(line: Optional[int] = None, column: Optional[int] = None) -> str:
    """Formatea la ubicación del error para mensajes legibles"""
    if line and column:
        return f"en línea {line}, columna {column}"
    elif line:
        return f"en línea {line}"
    else:
        return ""


def create_error_response(exception: BaseAPIException) -> Dict[str, Any]:
    """Crea una respuesta JSON estructurada para una excepción"""
    return {
        "success": False,
        "error_type": exception.error_code,
        "message": exception.message,
        "details": exception.details
    }


# =============================================
# EJEMPLOS DE USO
# =============================================

if __name__ == "__main__":
    """Ejemplos de cómo lanzar cada tipo de error"""
    
    # Ejemplo 1: LexerError
    try:
        raise InvalidCharacterError(char="@", line=5, column=12)
    except LexerError as e:
        print("LexerError:", e.to_dict())
    
    # Ejemplo 2: ParserError
    try:
        raise UnexpectedTokenError(
            expected="END",
            found="IF",
            line=10,
            column=5
        )
    except ParserError as e:
        print("ParserError:", e.to_dict())
    
    # Ejemplo 3: AnalysisError
    try:
        raise UndefinedVariableError(variable="x", line=8)
    except AnalysisError as e:
        print("AnalysisError:", e.to_dict())
    
    # Ejemplo 4: ValidationError
    try:
        raise EmptyCodeError()
    except ValidationError as e:
        print("ValidationError:", e.to_dict())