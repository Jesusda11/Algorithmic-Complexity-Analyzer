"""
Modelos de datos para endpoints relacionados con LLM
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class TranslationRequest(BaseModel):
    """Solicitud de traducción de lenguaje natural"""
    natural_language: str = Field(
        ...,
        description="Descripción del algoritmo en lenguaje natural",
        min_length=10,
        max_length=5000,
        examples=[
            "Crea un algoritmo que busque un elemento en un arreglo ordenado dividiéndolo por la mitad"
        ]
    )


class TranslationResponse(BaseModel):
    """Respuesta de traducción"""
    success: bool
    pseudocode: str
    warnings: List[str] = []


class VerificationRequest(BaseModel):
    """Solicitud de verificación de análisis"""
    pseudocode: str = Field(..., min_length=1)
    analysis_result: dict = Field(..., description="Resultado del análisis de complejidad")


class VerificationResponse(BaseModel):
    """Respuesta de verificación"""
    verified: bool
    is_correct: Optional[bool] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    issues: List[str] = []
    suggestions: List[str] = []
    alternative_complexity: Optional[str] = None
    reason: Optional[str] = None


class EnhancedAnalysisRequest(BaseModel):
    """Análisis mejorado con asistencia de LLM"""
    pseudocode: str = Field(..., min_length=1)
    analyze_recursion: bool = True
    classify_patterns: bool = True
    use_llm_verification: bool = False  # Opcional
    use_llm_explanation: bool = False   # Opcional
    target_audience: Literal["estudiante", "profesional", "principiante"] = "estudiante"