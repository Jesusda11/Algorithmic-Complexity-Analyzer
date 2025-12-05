"""
Modelos de Response (DTOs de salida)
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum


class TokenInfo(BaseModel):
    """Información de un token"""
    type: str
    value: str
    line: int
    column: int


class RecursionType(str, Enum):
    """Tipos de recursión"""
    DIRECT = "direct"
    INDIRECT = "indirect"
    TAIL = "tail"
    NONE = "none"


class DepthPattern(str, Enum):
    """Patrones de profundidad"""
    LINEAR = "linear"
    TREE = "tree"
    DIVIDE_AND_CONQUER = "divide_and_conquer"
    UNKNOWN = "unknown"


class RecursionInfoResponse(BaseModel):
    """Información de recursión de un procedimiento"""
    is_recursive: bool
    recursion_type: RecursionType
    call_count: int
    depth_pattern: DepthPattern
    subproblem: str
    has_combining_work: bool


class RecurrenceSolutionResponse(BaseModel):
    """Solución de una relación de recurrencia"""
    relation: str
    solution: str
    method: str
    explanation: str


class PatternType(str, Enum):
    """Tipos de patrones algorítmicos"""
    BINARY_SEARCH = "Búsqueda Binaria"
    LINEAR_SEARCH = "Búsqueda Lineal"
    MERGE_SORT = "Merge Sort"
    QUICK_SORT = "Quick Sort"
    FIBONACCI = "Fibonacci"
    FACTORIAL = "Factorial"
    TOWER_OF_HANOI = "Torres de Hanoi"
    GCD_EUCLIDEAN = "MCD (Euclides)"
    POWER_RECURSIVE = "Potencia Recursiva"
    KARATSUBA = "Karatsuba"
    N_QUEENS = "N-Reinas"
    PERMUTATIONS = "Permutaciones"
    UNKNOWN = "Desconocido"


class PatternClassificationResponse(BaseModel):
    """Clasificación de patrón algorítmico"""
    pattern: PatternType
    complexity: str
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    characteristics: Optional[List[str]] = None


class ComplexityResponse(BaseModel):
    """Complejidad computacional"""
    big_o: str = Field(description="Peor caso - O(n)")
    omega: str = Field(description="Mejor caso - Ω(n)")
    theta: str = Field(description="Caso promedio - Θ(n)")
    explanation: str
    steps: List[str] = Field(description="Pasos del análisis")


class ProcedureAnalysisResponse(BaseModel):
    """Análisis detallado de un procedimiento"""
    name: str
    recursion_info: RecursionInfoResponse
    recurrence_solution: Optional[RecurrenceSolutionResponse] = None
    pattern: Optional[PatternClassificationResponse] = None
    complexity: str


class AnalysisResponse(BaseModel):
    """Respuesta completa del análisis"""
    success: bool
    
    # Resultados principales
    complexity: ComplexityResponse
    
    # Análisis por procedimiento
    procedures: Optional[Dict[str, ProcedureAnalysisResponse]] = None
    
    # Información adicional (opcional)
    tokens: Optional[List[TokenInfo]] = None
    ast: Optional[Dict[str, Any]] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=lambda: {
            "lines_of_code": 0,
            "num_tokens": 0,
            "num_procedures": 0,
            "num_classes": 0
        }
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "complexity": {
                    "big_o": "n * log(n)",
                    "omega": "n * log(n)",
                    "theta": "n * log(n)",
                    "explanation": "Algoritmo de ordenamiento por mezcla",
                    "steps": ["Divide el arreglo...", "Combina O(n)..."]
                },
                "procedures": {
                    "MergeSort": {
                        "name": "MergeSort",
                        "recursion_info": {
                            "is_recursive": True,
                            "recursion_type": "direct",
                            "call_count": 2,
                            "depth_pattern": "divide_and_conquer",
                            "subproblem": "n/2",
                            "has_combining_work": True
                        },
                        "pattern": {
                            "pattern": "Merge Sort",
                            "complexity": "O(n log n)",
                            "confidence": 0.99,
                            "explanation": "T(n) = 2T(n/2) + O(n)"
                        },
                        "complexity": "O(n log n)"
                    }
                },
                "metadata": {
                    "lines_of_code": 45,
                    "num_tokens": 234,
                    "num_procedures": 2,
                    "num_classes": 0
                }
            }
        }


class ErrorResponse(BaseModel):
    """Respuesta de error"""
    success: bool = False
    error_type: str
    message: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error_type": "SyntaxError",
                "message": "Error en línea 5: Se esperaba 'end' pero se encontró 'fi'",
                "details": {
                    "line": 5,
                    "column": 10
                }
            }
        }


class HealthResponse(BaseModel):
    """Estado de salud del servicio"""
    status: str
    version: str
    uptime_seconds: float
    endpoints: List[str]