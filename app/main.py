# app/main.py
"""
Aplicación FastAPI - Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import time

# Controladores
from app.controllers import analysis_controller, health_controller

# Configuración
from app.config import settings


# =====================================
# LIFECYCLE EVENTS
# =====================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eventos del ciclo de vida de la aplicación"""
    # Startup
    print("🚀 Iniciando Analizador de Complejidad API...")
    print(f"📍 Entorno: {settings.ENVIRONMENT}")
    print(f"🔧 Debug: {settings.DEBUG}")
    
    yield
    
    # Shutdown
    print("🛑 Cerrando Analizador de Complejidad API...")


# =====================================
# APLICACIÓN FASTAPI
# =====================================

app = FastAPI(
    title=settings.APP_NAME,
    description="""
    ## Analizador de Complejidad Algorítmica

    API REST para análisis automático de complejidad computacional de algoritmos en pseudocódigo.

    ### Características principales:

    * **Análisis de complejidad:** Calcula O (peor caso), Ω (mejor caso) y Θ (caso promedio)
    * **Detección de recursión:** Identifica recursión directa, indirecta y de cola
    * **Resolución de recurrencias:** Usa Master Theorem y análisis directo
    * **Clasificación de patrones:** Detecta algoritmos clásicos (Binary Search, Merge Sort, etc.)
    * **Análisis detallado:** Proporciona pasos del razonamiento

    ### Endpoints disponibles:

    * `POST /api/v1/analysis/analyze` - Analizar pseudocódigo
    * `POST /api/v1/analysis/analyze-file` - Analizar archivo .txt
    * `POST /api/v1/analysis/batch-analyze` - Analizar múltiples algoritmos
    * `GET /api/v1/health` - Estado del servicio
    * `GET /api/v1/metrics` - Métricas del sistema

    ### Ejemplo de uso:

    ```python
    import requests

    response = requests.post(
        "http://localhost:8000/api/v1/analysis/analyze",
        json={
            "code": "procedure Factorial(n)\\nbegin\\n...\\nend",
            "enable_patterns": True
        }
    )

    result = response.json()
    print(f"Complejidad: {result['complexity']['big_o']}")
    ```
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# =====================================
# CORS MIDDLEWARE
# =====================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================
# ROUTERS
# =====================================

app.include_router(analysis_controller.router)
app.include_router(health_controller.router)


# =====================================
# ROOT ENDPOINT
# =====================================

@app.get("/", include_in_schema=False)
async def root():
    """Redirige a la documentación"""
    return RedirectResponse(url="/docs")


@app.get("/api/v1", tags=["Info"])
async def api_info():
    """Información de la API"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "description": "API de Análisis de Complejidad Algorítmica",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "analyze": "/api/v1/analysis/analyze",
            "analyze_file": "/api/v1/analysis/analyze-file",
            "batch_analyze": "/api/v1/analysis/batch-analyze"
        }
    }


# =====================================
# ERROR HANDLERS
# =====================================

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handler para errores de validación"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error_type": "ValidationError",
            "message": "Error en los datos de entrada",
            "details": exc.errors()
        }
    )


# =====================================
# MAIN (para desarrollo)
# =====================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )


