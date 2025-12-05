# ============================================================
# app/config.py
# Configuración centralizada de la API de Análisis de Complejidad
# ============================================================

from pydantic_settings import BaseSettings
from typing import List, Literal, Optional, Dict


# ============================================================
# Configuración principal
# ============================================================

class Settings(BaseSettings):
    # --------------------------------------------------------
    # App
    # --------------------------------------------------------
    APP_NAME: str = "Complexity Analyzer API"
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    DEBUG: bool = True

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --------------------------------------------------------
    # CORS
    # --------------------------------------------------------
    LOCAL_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:4200",
        "http://localhost:8080",
    ]

    ALLOW_ALL_ORIGINS: bool = False  # Nunca en producción

    def get_allowed_origins(self) -> List[str]:
        """Determina automáticamente los orígenes permitidos."""
        if self.ALLOW_ALL_ORIGINS and self.ENVIRONMENT != "production":
            return ["*"]
        return self.LOCAL_ORIGINS

    # --------------------------------------------------------
    # Límites del sistema
    # --------------------------------------------------------
    MAX_CODE_SIZE: int = 30000  # bytes (30 KB)
    MAX_CACHE_SIZE: int = 100
    ANALYSIS_TIMEOUT: int = 30  # segundos

    # --------------------------------------------------------
    # Soporte para LLM
    # --------------------------------------------------------
    LLM_PROVIDER: Literal["openai", "anthropic", "gemini", "none"] = "none"

    # API KEYS (se cargan desde .env)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: Optional[str] = None

    # Modelos recomendados
    LLM_MODELS: Dict[str, str] = {
        "openai": "gpt-4.1-mini",
        "anthropic": "claude-3-5-sonnet",
        "gemini": "gemini-2.5-pro",
    }

    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 60

    # Features activables
    ENABLE_LLM_TRANSLATION: bool = False
    ENABLE_LLM_VERIFICATION: bool = False
    ENABLE_LLM_PATTERN_ASSIST: bool = False
    ENABLE_LLM_EXPLANATION: bool = False

    # ============================================================
    # VALIDACIONES
    # ============================================================

    def is_llm_enabled(self) -> bool:
        """Retorna si hay un LLM activado y con features habilitadas."""
        if self.LLM_PROVIDER == "none":
            return False
        return any([
            self.ENABLE_LLM_TRANSLATION,
            self.ENABLE_LLM_VERIFICATION,
            self.ENABLE_LLM_PATTERN_ASSIST,
            self.ENABLE_LLM_EXPLANATION,
        ])

    def get_active_api_key(self) -> Optional[str]:
        """Obtiene la API key según el proveedor seleccionado."""
        mapping = {
            "openai": self.OPENAI_API_KEY,
            "anthropic": self.ANTHROPIC_API_KEY,
            "gemini": self.GEMINI_API_KEY,
        }
        return mapping.get(self.LLM_PROVIDER)

    def get_active_model(self) -> Optional[str]:
        if hasattr(self, "GEMINI_MODEL") and self.GEMINI_MODEL:
            return self.GEMINI_MODEL

        return self.LLM_MODELS.get(self.LLM_PROVIDER)


    def validate_llm_config(self) -> tuple[bool, str]:
        """Valida que el LLM esté bien configurado."""
        if self.LLM_PROVIDER == "none":
            return True, "LLM deshabilitado."

        api_key = self.get_active_api_key()
        model = self.get_active_model()

        if not api_key:
            return False, f"ERROR: Falta API key para provider '{self.LLM_PROVIDER}'"

        if len(api_key) < 20:
            return False, "ERROR: API key demasiado corta o inválida."

        if not model:
            return False, f"ERROR: No hay modelo configurado para '{self.LLM_PROVIDER}'"

        # Validación rápida proveedor ↔ modelo
        if self.LLM_PROVIDER == "openai" and not model.startswith("gpt"):
            return False, "Modelo inválido para OpenAI."
        if self.LLM_PROVIDER == "anthropic" and "claude" not in model:
            return False, "Modelo inválido para Anthropic."
        if self.LLM_PROVIDER == "gemini" and "gemini" not in model:
            return False, "Modelo inválido para Gemini."

        return True, "Configuración LLM válida."

    # --------------------------------------------------------
    # Debug helper
    # --------------------------------------------------------
    def summary(self) -> Dict:
        """Retorna estado resumido de configuración."""
        return {
            "app": self.APP_NAME,
            "env": self.ENVIRONMENT,
            "debug": self.DEBUG,
            "host": self.HOST,
            "port": self.PORT,
            "llm_provider": self.LLM_PROVIDER,
            "llm_enabled": self.is_llm_enabled(),
            "model": self.get_active_model(),
            "allowed_origins": self.get_allowed_origins(),
        }

    # --------------------------------------------------------
    # Config .env
    # --------------------------------------------------------
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton global
settings = Settings()

