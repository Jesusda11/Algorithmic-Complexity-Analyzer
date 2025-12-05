# ================================================================
# app/config.py
"""
Configuración de la aplicación
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Aplicación
    APP_NAME: str = "Analizador de Complejidad API"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React/Next.js
        "http://localhost:5173",  # Vite
        "http://localhost:4200",  # Angular
        "http://localhost:8080",  # Vue
        "*"  # TODO: Restringir en producción
    ]
    
    # Límites
    MAX_CODE_SIZE: int = 100000  # 100KB
    MAX_CACHE_SIZE: int = 100
    
    # Timeouts
    ANALYSIS_TIMEOUT: int = 30  # segundos
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


