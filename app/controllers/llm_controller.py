"""
Controlador para endpoints relacionados con LLM
"""

from fastapi import APIRouter, HTTPException, status
from app.models.llm_models import (
    TranslationRequest, TranslationResponse,
    VerificationRequest, VerificationResponse
)
from app.services.llm_assistant_service import llm_assistant
from app.config import settings
import logging

router = APIRouter(prefix="/api/v1/llm", tags=["LLM Assistant"])
logger = logging.getLogger(__name__)


@router.get("/status", summary="Estado del LLM")
async def llm_status():
    """Verifica el estado del servicio LLM"""
    from app.services.llm_service import llm_client
    
    return {
        "provider": settings.LLM_PROVIDER,
        "available": llm_client.is_available(),
        "features": {
            "translation": settings.ENABLE_LLM_TRANSLATION,
            "verification": settings.ENABLE_LLM_VERIFICATION,
            "pattern_assist": settings.ENABLE_LLM_PATTERN_ASSIST,
            "explanation": settings.ENABLE_LLM_EXPLANATION
        }
    }


@router.post(
    "/translate",
    response_model=TranslationResponse,
    summary="Traducir lenguaje natural a pseudocódigo"
)
async def translate_to_pseudocode(request: TranslationRequest):
    """
    Traduce descripción en lenguaje natural a pseudocódigo estructurado
    
    **Ejemplo:**
```json
    {
        "natural_language": "Algoritmo que ordena un arreglo dividiendo en mitades y mezclando"
    }
```
    """
    try:
        pseudocode = await llm_assistant.translate_to_pseudocode(
            request.natural_language
        )
        
        return TranslationResponse(
            success=True,
            pseudocode=pseudocode,
            warnings=[]
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en traducción: {str(e)}"
        )


@router.post(
    "/verify",
    response_model=VerificationResponse,
    summary="Verificar análisis de complejidad"
)
async def verify_analysis(request: VerificationRequest):
    """Verifica si un análisis de complejidad es correcto usando LLM"""
    try:
        verification = await llm_assistant.verify_analysis(
            pseudocode=request.pseudocode,
            our_analysis=request.analysis_result,
            steps=request.analysis_result.get("steps", [])
        )
        
        return VerificationResponse(
            verified=verification.get("verified", False),
            is_correct=verification.get("is_correct"),
            confidence=verification.get("confidence"),
            issues=verification.get("issues", []),
            suggestions=verification.get("suggestions", []),
            alternative_complexity=verification.get("alternative_complexity"),
            reason=verification.get("reason")
        )
    
    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )