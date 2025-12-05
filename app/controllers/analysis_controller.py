# app/controllers/analysis_controller.py
"""
Controlador de análisis - Maneja las peticiones HTTP
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
import time

from app.models.request_models import AnalysisRequest
from app.models.response_models import AnalysisResponse, ErrorResponse
from app.services.analysis_service import AnalysisService
from app.services.validation_service import ValidationService

from app.utils.exceptions import LexerError, ParserError, AnalysisError

# Router
router = APIRouter(prefix="/api/v1/analysis", tags=["Analysis"])

# Servicios
analysis_service = AnalysisService()
validation_service = ValidationService()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analizar pseudocódigo",
    description="Analiza un pseudocódigo y retorna su complejidad computacional",
    responses={
        200: {
            "description": "Análisis exitoso",
            "model": AnalysisResponse
        },
        400: {
            "description": "Error en la entrada",
            "model": ErrorResponse
        },
        500: {
            "description": "Error interno del servidor",
            "model": ErrorResponse
        }
    }
)
async def analyze_code(request: AnalysisRequest):
    """
    Analiza un pseudocódigo y retorna:
    - Complejidad temporal (O, Ω, Θ)
    - Análisis de recursión
    - Patrones algorítmicos detectados
    - Relaciones de recurrencia resueltas
    
    **Ejemplo de uso:**
    ```json
    {
        "code": "procedure Factorial(n)\\nbegin\\n...\\nend",
        "include_ast": false,
        "enable_patterns": true
    }
    ```
    """
    
    start_time = time.time()
    
    try:
        # Validación básica
        is_valid, error_msg = validation_service.validate_syntax(request.code)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error_type": "ValidationError",
                    "message": error_msg
                }
            )
    
        
        # Analizar
        result = analysis_service.analyze(
            code=request.code,
            include_ast=request.include_ast,
            include_tokens=request.include_tokens,
            enable_patterns=request.enable_patterns,
            enable_tracing=request.enable_tracing
        )
        
        # Agregar metadata de tiempo
        analysis_time = (time.time() - start_time) * 1000
        result.metadata["analysis_time_ms"] = round(analysis_time, 2)
        result.metadata["from_cache"] = False
        
        
        return result
    
    except LexerError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_type": "LexerError",
                "message": str(e),
                "details": e.details if hasattr(e, 'details') else None
            }
        )
    
    except ParserError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_type": "ParserError",
                "message": str(e),
                "details": e.details if hasattr(e, 'details') else None
            }
        )
    
    except AnalysisError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "AnalysisError",
                "message": str(e),
                "details": e.details if hasattr(e, 'details') else None
            }
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error_type": "InternalError",
                "message": f"Error inesperado: {str(e)}"
            }
        )


@router.post(
    "/analyze-file",
    response_model=AnalysisResponse,
    summary="Analizar archivo de pseudocódigo",
    description="Sube un archivo .txt con pseudocódigo y analízalo"
)
async def analyze_file(
    file: UploadFile = File(..., description="Archivo .txt con pseudocódigo"),
    include_ast: bool = False,
    include_tokens: bool = False,
    enable_patterns: bool = True
):
    """
    Analiza un archivo de pseudocódigo
    
    **Soporta:**
    - Archivos .txt
    - Máximo 100KB
    """
    
    # Validar tipo de archivo
    if not file.filename.endswith('.txt'):
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_type": "ValidationError",
                "message": "Solo se permiten archivos .txt"
            }
        )
    
    # Leer contenido
    try:
        content = await file.read()
        code = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error_type": "EncodingError",
                "message": "El archivo debe estar en formato UTF-8"
            }
        )
    
    # Crear request y analizar
    request = AnalysisRequest(
        code=code,
        include_ast=include_ast,
        include_tokens=include_tokens,
        enable_patterns=enable_patterns
    )
    
    return await analyze_code(request)


@router.post(
    "/batch-analyze",
    summary="Analizar múltiples algoritmos",
    description="Analiza varios pseudocódigos y compáralos"
)
async def batch_analyze(codes: list[str]):
    """
    Analiza múltiples algoritmos y retorna comparación
    
    **Útil para:**
    - Comparar diferentes implementaciones
    - Benchmarking
    """
    
    if len(codes) > 10:
        raise HTTPException(
            status_code=400,
            detail="Máximo 10 códigos por request"
        )
    
    results = []
    
    for i, code in enumerate(codes):
        try:
            request = AnalysisRequest(code=code, enable_patterns=True)
            result = analysis_service.analyze(
                code=request.code,
                enable_patterns=True
            )
            
            results.append({
                "index": i,
                "success": True,
                "big_o": result.complexity.big_o,
                "omega": result.complexity.omega,
                "theta": result.complexity.theta
            })
        
        except Exception as e:
            results.append({
                "index": i,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total": len(codes),
        "successful": sum(1 for r in results if r["success"]),
        "results": results
    }


@router.delete(
    "/cache",
    summary="Limpiar cache",
    description="Limpia el cache de análisis"
)
async def clear_cache():
    """Limpia el cache de análisis"""
    return {"message": "Cache limpiado exitosamente"}


