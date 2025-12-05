"""
Servicio que coordina las funcionalidades asistidas por LLM
"""

from typing import Dict, Optional, List
import json
import logging
from app.services.llm_service import llm_client
from app.utils.llm_prompts import LLMPrompts
from app.config import settings

logger = logging.getLogger(__name__)


class LLMAssistantService:
    """Servicio para funcionalidades asistidas por LLM"""
    
    def __init__(self):
        self.prompts = LLMPrompts()
        self._check_availability()
    
    def _check_availability(self):
        """Verifica si el LLM está disponible"""
        if not llm_client.is_available():
            logger.warning("⚠️  LLM client not available. Features will be disabled.")
    
    async def translate_to_pseudocode(self, natural_language: str) -> str:
        """
        Traduce descripción en lenguaje natural a pseudocódigo
        
        Args:
            natural_language: Descripción del algoritmo
            
        Returns:
            Pseudocódigo estructurado
        """
        if not settings.ENABLE_LLM_TRANSLATION:
            raise ValueError("LLM translation is disabled in settings")
        
        if not llm_client.is_available():
            raise ValueError("LLM client not initialized")
        
        try:
            logger.info("🔄 Translating natural language to pseudocode...")
            
            prompts = self.prompts.translate_natural_language_to_pseudocode(
                natural_language
            )
            
            pseudocode = await llm_client.generate(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.1  # Muy determinístico
            )
            
            # Limpiar respuesta
            pseudocode = self._clean_pseudocode_response(pseudocode)
            
            logger.info("✅ Translation completed")
            return pseudocode
        
        except Exception as e:
            logger.error(f"❌ Translation error: {str(e)}")
            raise
    
    async def verify_analysis(
        self,
        pseudocode: str,
        our_analysis: Dict,
        steps: List[str]
    ) -> Dict:
        """
        Verifica análisis de complejidad usando LLM
        
        Returns:
            Dict con verificación y sugerencias
        """
        if not settings.ENABLE_LLM_VERIFICATION:
            return {
                "verified": False,
                "reason": "LLM verification disabled in settings"
            }
        
        if not llm_client.is_available():
            return {
                "verified": False,
                "reason": "LLM client not available"
            }
        
        try:
            logger.info("🔍 Verifying complexity analysis with LLM...")
            
            prompts = self.prompts.verify_complexity_analysis(
                pseudocode, our_analysis, steps
            )
            
            response = await llm_client.generate(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.2
            )
            
            # Parsear JSON
            verification = self._parse_json_response(response)
            
            logger.info(f"✅ Verification: {verification.get('is_correct', 'unknown')}")
            return verification
        
        except Exception as e:
            logger.error(f"❌ Verification error: {str(e)}")
            return {
                "verified": False,
                "error": str(e),
                "fallback": True
            }
    
    async def assist_pattern_classification(
        self,
        pseudocode: str,
        recursion_info: str,
        complexity: str
    ) -> Dict:
        """
        Asiste en clasificación de patrones
        
        Returns:
            Dict con patrón detectado y confianza
        """
        if not settings.ENABLE_LLM_PATTERN_ASSIST:
            return {
                "assisted": False,
                "reason": "LLM pattern assist disabled"
            }
        
        if not llm_client.is_available():
            return {
                "assisted": False,
                "reason": "LLM client not available"
            }
        
        try:
            logger.info("🎯 Classifying pattern with LLM assistance...")
            
            prompts = self.prompts.classify_algorithm_pattern(
                pseudocode, str(recursion_info), complexity
            )
            
            response = await llm_client.generate(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.3
            )
            
            classification = self._parse_json_response(response)
            
            logger.info(f"✅ Pattern: {classification.get('pattern', 'unknown')}")
            return classification
        
        except Exception as e:
            logger.error(f"❌ Pattern classification error: {str(e)}")
            return {
                "assisted": False,
                "error": str(e)
            }
    
    async def enhance_explanation(
        self,
        pseudocode: str,
        complexity_result: Dict,
        target_audience: str = "estudiante"
    ) -> str:
        """
        Genera explicación mejorada
        
        Returns:
            Explicación educativa
        """
        if not settings.ENABLE_LLM_EXPLANATION:
            # Fallback a explicación original
            return complexity_result.get("explanation", "")
        
        if not llm_client.is_available():
            return complexity_result.get("explanation", "")
        
        try:
            logger.info("📝 Enhancing explanation with LLM...")
            
            prompts = self.prompts.enhance_explanation(
                pseudocode, complexity_result, target_audience
            )
            
            explanation = await llm_client.generate(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                temperature=0.5
            )
            
            logger.info("✅ Explanation enhanced")
            return explanation
        
        except Exception as e:
            logger.error(f"❌ Explanation enhancement error: {str(e)}")
            # Fallback
            return complexity_result.get("explanation", "")
    
    def _clean_pseudocode_response(self, response: str) -> str:
        """Limpia respuesta del LLM"""
        # Remover bloques de código markdown
        response = response.replace("```pseudocode", "").replace("```", "")
        
        # Remover prefijos comunes
        prefixes = ["pseudocódigo:", "pseudocode:", "resultado:"]
        for prefix in prefixes:
            if response.lower().startswith(prefix):
                response = response[len(prefix):].strip()
        
        return response.strip()
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parsea respuesta JSON del LLM"""
        try:
            # Buscar JSON en la respuesta
            start = response.find("{")
            end = response.rfind("}") + 1
            
            if start != -1 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in response")
                return {"raw_response": response, "parsed": False}
        
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {str(e)}")
            return {
                "error": "Invalid JSON",
                "raw_response": response,
                "parsed": False
            }


# Singleton
llm_assistant = LLMAssistantService()