"""
Clasificador de Patrones Algorítmicos Conocidos
Basado en la información de recursion.py y recurrence.py
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class PatternType(Enum):
    BINARY_SEARCH = "Búsqueda Binaria"
    MERGE_SORT = "Merge Sort"
    QUICK_SORT = "Quick Sort"
    FIBONACCI = "Fibonacci (naïve)"
    UNKNOWN = "Desconocido"


@dataclass
class PatternClassification:
    pattern: PatternType
    complexity: str
    confidence: float  # 0.0 a 1.0
    explanation: str


class PatternClassifier:
    """
    Clasifica una función recursiva según patrones algorítmicos conocidos
    usando la información de RecursionInfo y RecurrenceSolution
    """

    def __init__(self):
        # Umbrales de confianza
        self.HIGH_CONF = 0.95
        self.MEDIUM_CONF = 0.75

    def classify(self,
                 func_name: str,
                 recursion_info: Any,
                 recurrence_solution: Any,
                 recurrence_relation: Any = None) -> PatternClassification:
        """
        Clasifica combinando toda la información disponible
        """
        if not recursion_info.is_recursive:
            return PatternClassification(
                pattern=PatternType.UNKNOWN,
                complexity="No recursivo",
                confidence=1.0,
                explanation="La función no es recursiva"
            )

        info = recursion_info
        sol = recurrence_solution
        rel = recurrence_relation

        # -------------------------------------------------
        # 1. Búsqueda Binaria
        # -------------------------------------------------
        if (info.call_count <= 2 and
            info.depth_pattern == "divide_and_conquer" and
            info.subproblem == "n/2" and
            getattr(rel, "a", 0) == 1 and
            "log" in sol.complexity.lower() and
            "n" not in sol.complexity.lower().replace("log", "")):
            return PatternClassification(
                pattern=PatternType.BINARY_SEARCH,
                complexity="O(log n)",
                confidence=1.0,
                explanation="1 llamada activa, divide en n/2, costo constante → Búsqueda Binaria"
            )

        # -------------------------------------------------
        # 2. Merge Sort - Detección robusta
        # -------------------------------------------------
        if (info.depth_pattern == "divide_and_conquer"
            and info.subproblem == "n/2"
            and info.call_count >= 2
            and "n log" in sol.complexity.lower()
            and getattr(rel, "a", 0) == 2
            and getattr(rel, "f_complexity", "").strip().lower() == "n"):

            return PatternClassification(
                pattern=PatternType.MERGE_SORT,
                complexity="O(n log n)",
                confidence=0.99,
                explanation="T(n) = 2T(n/2) + O(n) → Merge Sort clásico"
            )        

        # -------------------------------------------------
        # 3. Quick Sort (promedio)
        # -------------------------------------------------
        if (info.call_count >= 2 and
            info.depth_pattern == "divide_and_conquer" and
            info.subproblem in ("n/2", "unknown") and
            not info.has_combining_work and
            "n log" in sol.complexity.lower()):
            # Distinguir de MergeSort por ausencia de merge
            return PatternClassification(
                pattern=PatternType.QUICK_SORT,
                complexity="O(n log n) promedio, O(n²) peor caso",
                confidence=0.95,
                explanation="2 llamadas, divide (posiblemente desbalanceado), sin fase de merge → Quick Sort"
            )

        # -------------------------------------------------
        # 4. Fibonacci naïf
        # -------------------------------------------------
        if (info.call_count >= 2 and
            info.subproblem == "n-1" and
            info.depth_pattern == "tree" and
            ("2^n" in sol.complexity or "1.6" in sol.complexity or "φ^n" in sol.complexity)):
            return PatternClassification(
                pattern=PatternType.FIBONACCI,
                complexity="O(2^n)",
                confidence=1.0,
                explanation="2 llamadas recursivas de tamaño n-1 → Fibonacci naïf"
            )

        # -------------------------------------------------
        # Caso genérico: usar lo que diga el solver
        # -------------------------------------------------
        return PatternClassification(
            pattern=PatternType.UNKNOWN,
            complexity=sol.complexity,
            confidence=0.6,
            explanation=f"Patrón no reconocido. Complejidad estimada: {sol.complexity}"
        )

    def print_classification(self, classification: PatternClassification, func_name: str):
        print(f"\n ANÁLISIS DE PATRÓN - {func_name}")
        print("=" * 60)
        print(f"   Patrón detectado:     {classification.pattern.value}")
        print(f"   Complejidad:          {classification.complexity}")
        print(f"   Confianza:            {classification.confidence:.1%}")
        print(f"   Explicación:          {classification.explanation}")
        print("=" * 60)


    