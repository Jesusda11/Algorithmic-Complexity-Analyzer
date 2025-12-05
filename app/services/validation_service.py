# app/services/validation_service.py
from typing import Optional


class ValidationService:
    """Valida que el pseudocódigo sea sintácticamente correcto"""
    
    def validate_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """
        Valida la sintaxis básica del pseudocódigo
        
        Returns:
            (is_valid, error_message)
        """
        
        if not code.strip():
            return False, "El código no puede estar vacío"
        
        if len(code) > 100000:
            return False, "El código excede el tamaño máximo (100KB)"
        
        begin_count = code.lower().count('begin')
        end_count = code.lower().count('end')
        
        if begin_count != end_count:
            return False, f"BEGIN/END desbalanceados: {begin_count} begin, {end_count} end"
        
        return True, None
    
    def estimate_complexity(self, code: str) -> str:
        """Estima rápidamente si el análisis será costoso"""
        lines = code.count('\n')
        
        if lines < 50:
            return "simple"
        elif lines < 200:
            return "medium"
        else:
            return "complex"