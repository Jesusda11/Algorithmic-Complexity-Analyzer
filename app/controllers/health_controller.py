# ================================================================
# app/controllers/health_controller.py
"""
Controlador de salud del servicio
"""
from fastapi import APIRouter
import time
import psutil
import os

from app.models.response_models import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["Health"])

# Tiempo de inicio
START_TIME = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Estado de salud",
    description="Verifica el estado del servicio"
)
async def health_check():
    """
    Verifica que el servicio esté funcionando correctamente
    
    **Retorna:**
    - Estado del servicio
    - Versión
    - Tiempo activo
    - Endpoints disponibles
    """
    
    uptime = time.time() - START_TIME
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        uptime_seconds=round(uptime, 2),
        endpoints=[
            "/api/v1/analysis/analyze",
            "/api/v1/analysis/analyze-file",
            "/api/v1/analysis/batch-analyze",
            "/api/v1/health",
            "/api/v1/metrics"
        ]
    )


@router.get(
    "/metrics",
    summary="Métricas del sistema",
    description="Retorna métricas de uso del servidor"
)
async def metrics():
    """
    Métricas del sistema
    
    **Incluye:**
    - Uso de CPU
    - Uso de memoria
    - Número de análisis en cache
    """
    
    # Importar aquí para evitar dependencia circular
    from app.controllers.analysis_controller import cache_service
    
    process = psutil.Process(os.getpid())
    
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory": {
            "used_mb": round(process.memory_info().rss / 1024 / 1024, 2),
            "percent": process.memory_percent()
        },
        "cache": {
            "size": len(cache_service.cache),
            "max_size": cache_service.max_size
        },
        "uptime_seconds": round(time.time() - START_TIME, 2)
    }