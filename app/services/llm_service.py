"""
Cliente para Google Gemini
Servicio base para interactuar con el LLM
"""

import google.generativeai as genai
from typing import Optional
from app.config import settings
import logging
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


class LLMClient:
    """Cliente para interactuar con Google Gemini"""
    
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.model_name = settings.get_active_model()
        self._client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Inicializa el cliente de Gemini"""
        if self.provider != "gemini":
            logger.warning(f"LLM Provider is '{self.provider}', but LLMClient is Gemini-only")
            return
        
        if not settings.GEMINI_API_KEY:
            logger.error("GEMINI_API_KEY no configurada")
            return
        
        try:
            # Configurar Gemini
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Crear modelo
            self._client = genai.GenerativeModel(self.model_name)
            
            logger.info(f"✅ Gemini client initialized: {self.model_name}")
        
        except Exception as e:
            logger.error(f"❌ Error initializing Gemini: {str(e)}")
            self._client = None
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Genera respuesta del LLM
        
        Args:
            prompt: Prompt del usuario
            system_prompt: Instrucciones del sistema (se concatena al inicio)
            temperature: Override de temperatura
            
        Returns:
            Respuesta generada como string
        """
        if not self._client:
            raise ValueError("LLM client not initialized. Check your GEMINI_API_KEY")
        
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        
        try:
            # En Gemini, el system prompt se concatena al user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Configuración de generación
            generation_config = {
                "temperature": temp,
                "max_output_tokens": settings.LLM_MAX_TOKENS,
                "top_p": 0.95,
                "top_k": 40,
            }
            
            # Generar respuesta (ejecutar en thread pool para no bloquear)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
            )
            
            # Extraer texto
            if response.candidates and len(response.candidates) > 0:
                return response.candidates[0].content.parts[0].text
            else:
                raise ValueError("No response candidates from Gemini")
        
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """Verifica si el cliente está disponible"""
        return self._client is not None


# Singleton global
@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Factory function para obtener el cliente (singleton)"""
    return LLMClient()


llm_client = get_llm_client()