"""
Templates de prompts para diferentes tareas del LLM
Optimizados para Google Gemini
"""

from typing import Dict, List


class LLMPrompts:
    """Colección de prompts estructurados para el LLM"""
    
    @staticmethod
    def translate_natural_language_to_pseudocode(natural_language: str) -> Dict[str, str]:
        """Prompt para traducir lenguaje natural → pseudocódigo"""
        
        system_prompt = """Eres un experto en algoritmos y análisis de complejidad computacional.
Traduce descripciones de algoritmos en lenguaje natural a pseudocódigo estructurado.

SINTAXIS OBLIGATORIA:
- Bloques: begin ... end
- Asignación: 🡨 (o usar <- si no soportas Unicode)
- FOR: for i 🡨 1 to n do begin ... end
- WHILE: while (condicion) do begin ... end
- IF: if (condicion) then begin ... end else begin ... end
- CALL: call NombreProcedimiento(args)
- Comentarios: ► texto

REGLAS:
✅ Usa nombres descriptivos en español
✅ Sigue EXACTAMENTE la sintaxis especificada
✅ NO uses sintaxis de ningún lenguaje real (Java, Python, etc.)
✅ Retorna SOLO el pseudocódigo, sin explicaciones extra
"""
        
        user_prompt = f"""Traduce este algoritmo a pseudocódigo estructurado:

{natural_language}

IMPORTANTE: Usa la sintaxis especificada arriba."""
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    @staticmethod
    def verify_complexity_analysis(
        pseudocode: str,
        our_analysis: Dict,
        steps: List[str]
    ) -> Dict[str, str]:
        """Prompt para verificar análisis de complejidad"""
        
        system_prompt = """Eres un profesor experto en análisis de algoritmos.
Verifica si un análisis de complejidad computacional es correcto.

Evalúa:
1. ¿La complejidad O (peor caso) es correcta?
2. ¿La complejidad Ω (mejor caso) es correcta?
3. ¿La complejidad Θ (caso promedio) es correcta?
4. ¿Se aplicó correctamente el Teorema Maestro (si hay recursión)?
5. ¿El análisis es consistente?

FORMATO DE RESPUESTA (JSON):
{
  "is_correct": true/false,
  "confidence": 0.0-1.0,
  "issues": ["problema1", "problema2"],
  "suggestions": ["sugerencia1"],
  "alternative_complexity": "O(...)" o null
}
"""
        
        # Limitar steps para no saturar el prompt
        steps_preview = "\n".join(steps[:15]) if len(steps) > 15 else "\n".join(steps)
        
        user_prompt = f"""Verifica este análisis:

PSEUDOCÓDIGO:
```
{pseudocode}
```

ANÁLISIS REALIZADO:
- Peor caso: O({our_analysis.get('big_o', '?')})
- Mejor caso: Ω({our_analysis.get('omega', '?')})
- Caso promedio: Θ({our_analysis.get('theta', '?')})

PASOS DEL ANÁLISIS:
{steps_preview}

¿Es correcto? Responde en JSON como se especificó."""
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    @staticmethod
    def classify_algorithm_pattern(
        pseudocode: str,
        recursion_info: str,
        complexity: str
    ) -> Dict[str, str]:
        """Prompt para clasificar patrones algorítmicos"""
        
        system_prompt = """Eres un experto en algoritmos clásicos.
Identifica si un algoritmo corresponde a un patrón conocido.

PATRONES CONOCIDOS:
- Búsqueda Binaria: O(log n), 1 llamada recursiva, divide n/2
- MergeSort: O(n log n), 2 llamadas recursivas, divide n/2, tiene merge
- QuickSort: O(n log n) promedio, 2 llamadas, pivot
- Fibonacci: O(2^n), 2 llamadas recursivas, n-1
- Búsqueda Lineal: O(n), recorre secuencialmente
- Insertion Sort: O(n²), ordenamiento por inserción

FORMATO DE RESPUESTA (JSON):
{
  "pattern": "nombre del patrón" o "unknown",
  "confidence": 0.0-1.0,
  "reasoning": "explicación de 1-2 líneas",
  "typical_complexity": "O(...)"
}
"""
        
        user_prompt = f"""Clasifica este algoritmo:

PSEUDOCÓDIGO:
```
{pseudocode[:500]}...
```

INFO RECURSIÓN:
{recursion_info}

COMPLEJIDAD DETECTADA: {complexity}

¿A qué patrón clásico corresponde? Responde en JSON."""
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    @staticmethod
    def enhance_explanation(
        pseudocode: str,
        complexity_result: Dict,
        target_audience: str = "estudiante"
    ) -> Dict[str, str]:
        """Prompt para mejorar explicaciones"""
        
        audience_instructions = {
            "estudiante": "Explica como a un estudiante universitario de CS. Usa analogías simples.",
            "profesional": "Explicación técnica concisa para desarrolladores experimentados.",
            "principiante": "Explicación muy simple, asumiendo conocimientos básicos de programación."
        }
        
        system_prompt = f"""Eres un profesor de algoritmos explicando complejidad computacional.

AUDIENCIA: {audience_instructions.get(target_audience, audience_instructions['estudiante'])}

Tu explicación debe:
✅ Ser clara y educativa
✅ Explicar POR QUÉ la complejidad es esa
✅ Mencionar casos edge si existen
✅ Sugerir optimizaciones si son obvias
❌ NO repetir lo que ya está en el análisis técnico
❌ NO usar fórmulas matemáticas complejas
"""
        
        user_prompt = f"""Genera una explicación educativa:

ALGORITMO:
```
{pseudocode[:400]}...
```

COMPLEJIDAD:
- Peor caso: O({complexity_result.get('big_o', '?')})
- Mejor caso: Ω({complexity_result.get('omega', '?')})
- Caso promedio: Θ({complexity_result.get('theta', '?')})

Explica de forma clara por qué tiene esta complejidad."""
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }