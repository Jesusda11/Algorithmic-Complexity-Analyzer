"""
Modelos de Request (DTOs de entrada)
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class AnalysisRequest(BaseModel):
    """Request para análisis de pseudocódigo"""
    code: str = Field(
        ..., 
        min_length=1,
        max_length=100000,
        description="Pseudocódigo a analizar",
        examples=["""
procedure Factorial(n)
begin
    if (n ≤ 1) then
    begin
        return 1
    end
    else
    begin
        return n * call Factorial(n - 1)
    end
end
        """]
    )
    
    include_ast: bool = Field(
        default=False,
        description="Si incluir el AST completo en la respuesta"
    )
    
    include_tokens: bool = Field(
        default=False,
        description="Si incluir los tokens en la respuesta"
    )
    
    enable_patterns: bool = Field(
        default=True,
        description="Si habilitar clasificación de patrones algorítmicos"
    )
    
    enable_tracing: bool = Field(
        default=False,
        description="Si generar traza de ejecución (requiere intérprete)"
    )
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('El código no puede estar vacío')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "code": "procedure BusquedaBinaria(A[], x, inicio, fin)\nbegin\n...\nend",
                "include_ast": False,
                "include_tokens": False,
                "enable_patterns": True
            }
        }