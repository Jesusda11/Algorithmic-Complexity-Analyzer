"""
Clasificador de Patrones Algorítmicos - VERSIÓN EXTENDIDA
Detecta más patrones clásicos de algoritmos
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class PatternType(Enum):
    # Búsqueda y ordenamiento
    BINARY_SEARCH = "Búsqueda Binaria"
    LINEAR_SEARCH = "Búsqueda Lineal"
    MERGE_SORT = "Merge Sort"
    QUICK_SORT = "Quick Sort"
    
    # Recursión clásica
    FIBONACCI = "Fibonacci (naïve)"
    FACTORIAL = "Factorial"
    TOWER_OF_HANOI = "Torres de Hanoi"
    
    # Divide y conquista
    KARATSUBA = "Multiplicación de Karatsuba"
    STRASSEN = "Multiplicación de Strassen"
    
    # Programación dinámica (si se detecta)
    FIBONACCI_DP = "Fibonacci (optimizado)"
    
    # Backtracking
    N_QUEENS = "N-Reinas (Backtracking)"
    PERMUTATIONS = "Generación de Permutaciones"
    
    # Otros
    GCD_EUCLIDEAN = "MCD (Euclides)"
    POWER_RECURSIVE = "Potencia Recursiva"
    
    UNKNOWN = "Desconocido"


@dataclass
class PatternClassification:
    pattern: PatternType
    complexity: str
    confidence: float  # 0.0 a 1.0
    explanation: str
    characteristics: list = None  # Lista de características detectadas


class PatternClassifier:
    """
    Clasifica funciones según patrones algorítmicos conocidos
    Versión extendida con más patrones
    """

    def __init__(self):
        self.HIGH_CONF = 0.95
        self.MEDIUM_CONF = 0.75
        self.LOW_CONF = 0.5

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
                explanation="La función no es recursiva",
                characteristics=[]
            )

        info = recursion_info
        sol = recurrence_solution
        rel = recurrence_relation

        # =============================================
        # DETECCIÓN POR NOMBRE DE FUNCIÓN (heurística adicional)
        # =============================================
        name_lower = func_name.lower()
        
        # -------------------------------------------------
        # 1. BÚSQUEDA BINARIA
        # -------------------------------------------------
        if (info.call_count == 1 and
            info.depth_pattern == "divide_and_conquer" and
            info.subproblem == "n/2" and
            getattr(rel, "a", 0) == 1 and
            "log" in sol.complexity.lower() and
            "n" not in sol.complexity.lower().replace("log", "")):
            
            # Verificar nombre para aumentar confianza
            confidence = 1.0
            if any(x in name_lower for x in ["busqueda", "search", "binari", "binary"]):
                confidence = 1.0
            
            return PatternClassification(
                pattern=PatternType.BINARY_SEARCH,
                complexity="O(log n)",
                confidence=confidence,
                explanation="T(n) = T(n/2) + O(1) → Una llamada, divide en mitades, costo constante",
                characteristics=[
                    "1 llamada recursiva activa",
                    "Reduce problema a la mitad",
                    "Sin trabajo de combinación",
                    "Típico de búsqueda en datos ordenados"
                ]
            )

        # -------------------------------------------------
        # 2. MERGE SORT
        # -------------------------------------------------
        if (info.depth_pattern == "divide_and_conquer"
            and info.subproblem == "n/2"
            and info.call_count >= 2
            and "n log" in sol.complexity.lower()
            and getattr(rel, "a", 0) == 2
            and getattr(rel, "f_complexity", "").strip().lower() == "n"
            and info.has_combining_work):

            confidence = 0.99
            if any(x in name_lower for x in ["merge", "ordenar", "sort"]):
                confidence = 1.0

            return PatternClassification(
                pattern=PatternType.MERGE_SORT,
                complexity="O(n log n)",
                confidence=confidence,
                explanation="T(n) = 2T(n/2) + O(n) → Divide en mitades, combina linealmente",
                characteristics=[
                    "2 llamadas recursivas",
                    "Divide en mitades exactas",
                    "Fase de merge O(n)",
                    "Estable y óptimo para ordenamiento por comparación"
                ]
            )

        # -------------------------------------------------
        # 3. QUICK SORT
        # -------------------------------------------------
        if (info.call_count >= 2 and
            info.depth_pattern == "divide_and_conquer" and
            info.subproblem in ("n/2", "unknown") and
            not info.has_combining_work and
            "n log" in sol.complexity.lower()):
            
            confidence = 0.90
            if any(x in name_lower for x in ["quick", "rapido"]):
                confidence = 0.98

            return PatternClassification(
                pattern=PatternType.QUICK_SORT,
                complexity="O(n log n) promedio, O(n²) peor caso",
                confidence=confidence,
                explanation="2 llamadas, partición posiblemente desbalanceada, sin merge",
                characteristics=[
                    "2 llamadas recursivas",
                    "División puede ser desbalanceada",
                    "Sin fase de combinación",
                    "In-place (eficiente en espacio)"
                ]
            )

        # -------------------------------------------------
        # 4. FIBONACCI NAÏF
        # -------------------------------------------------
        if (info.call_count == 2 and
            info.subproblem == "n-1" and
            info.depth_pattern == "tree" and
            ("2^n" in sol.complexity or "^n" in sol.complexity)):
            
            confidence = 1.0
            if any(x in name_lower for x in ["fib", "fibonacci"]):
                confidence = 1.0

            return PatternClassification(
                pattern=PatternType.FIBONACCI,
                complexity="O(2^n)",
                confidence=confidence,
                explanation="T(n) = T(n-1) + T(n-2) → Árbol binario exponencial",
                characteristics=[
                    "2 llamadas: F(n-1) y F(n-2)",
                    "Recalcula subproblemas repetidamente",
                    "Exponencial sin memoización",
                    "Mejora a O(n) con programación dinámica"
                ]
            )

        # -------------------------------------------------
        # 5. FACTORIAL
        # -------------------------------------------------
        if (info.call_count == 1 and
            info.subproblem == "n-1" and
            info.depth_pattern == "linear" and
            "n" in sol.complexity.lower() and
            "log" not in sol.complexity.lower() and
            "^" not in sol.complexity):
            
            confidence = 0.85
            if any(x in name_lower for x in ["fact", "factorial"]):
                confidence = 1.0

            return PatternClassification(
                pattern=PatternType.FACTORIAL,
                complexity="O(n)",
                confidence=confidence,
                explanation="T(n) = T(n-1) + O(1) → Recursión lineal simple",
                characteristics=[
                    "1 llamada recursiva",
                    "Reduce problema en 1",
                    "Trabajo constante por llamada",
                    "Clásico ejemplo de recursión lineal"
                ]
            )

        # -------------------------------------------------
        # 6. TORRES DE HANOI
        # -------------------------------------------------
        if (info.call_count == 2 and
            info.subproblem == "n-1" and
            info.depth_pattern == "tree" and
            "2^n" in sol.complexity):
            
            confidence = 0.80
            if any(x in name_lower for x in ["hanoi", "torre", "tower"]):
                confidence = 1.0

            return PatternClassification(
                pattern=PatternType.TOWER_OF_HANOI,
                complexity="O(2^n)",
                confidence=confidence,
                explanation="T(n) = 2T(n-1) + O(1) → 2^n movimientos mínimos",
                characteristics=[
                    "2 llamadas recursivas",
                    "Cada una con n-1 discos",
                    "Movimientos óptimos: 2^n - 1",
                    "Problema clásico de recursión"
                ]
            )

        # -------------------------------------------------
        # 7. MCD (EUCLIDES)
        # -------------------------------------------------
        if (info.call_count == 1 and
            info.depth_pattern in ("linear", "divide_and_conquer") and
            "log" in sol.complexity.lower() and
            info.subproblem in ("n%m", "mod", "unknown")):
            
            confidence = 0.70
            if any(x in name_lower for x in ["gcd", "mcd", "euclid"]):
                confidence = 0.95

            return PatternClassification(
                pattern=PatternType.GCD_EUCLIDEAN,
                complexity="O(log min(a,b))",
                confidence=confidence,
                explanation="Algoritmo de Euclides: reduce rápidamente el tamaño",
                characteristics=[
                    "1 llamada recursiva",
                    "Usa operación módulo",
                    "Logarítmico en el número menor",
                    "Muy eficiente para números grandes"
                ]
            )

        # -------------------------------------------------
        # 8. POTENCIA RECURSIVA (Divide y Conquista)
        # -------------------------------------------------
        if (info.call_count == 1 and
            info.subproblem == "n/2" and
            "log" in sol.complexity.lower() and
            info.depth_pattern == "divide_and_conquer"):
            
            confidence = 0.75
            if any(x in name_lower for x in ["pow", "power", "potencia", "exp"]):
                confidence = 0.95

            return PatternClassification(
                pattern=PatternType.POWER_RECURSIVE,
                complexity="O(log n)",
                confidence=confidence,
                explanation="Exponenciación rápida: x^n con log(n) multiplicaciones",
                characteristics=[
                    "1 llamada con n/2",
                    "Multiplica resultado consigo mismo",
                    "Mucho más rápido que O(n) lineal",
                    "Usado en criptografía"
                ]
            )

        # -------------------------------------------------
        # 9. KARATSUBA (Multiplicación rápida)
        # -------------------------------------------------
        if (info.call_count == 3 and
            info.subproblem == "n/2" and
            info.depth_pattern == "divide_and_conquer"):
            
            confidence = 0.80
            if any(x in name_lower for x in ["karatsuba", "fast_mult"]):
                confidence = 0.95

            return PatternClassification(
                pattern=PatternType.KARATSUBA,
                complexity="O(n^1.585)",
                confidence=confidence,
                explanation="T(n) = 3T(n/2) + O(n) → Multiplicación sub-cuadrática",
                characteristics=[
                    "3 llamadas recursivas (truco de Karatsuba)",
                    "Divide números en mitades",
                    "Mejor que O(n²) tradicional",
                    "Usado para números muy grandes"
                ]
            )

        # -------------------------------------------------
        # 10. BACKTRACKING (N-Reinas, Permutaciones)
        # -------------------------------------------------
        if (info.call_count >= 4 and
            info.depth_pattern == "tree" and
            "^n" in sol.complexity):
            
            confidence = 0.65
            if any(x in name_lower for x in ["queen", "reina", "permut", "backtrack"]):
                confidence = 0.90

            pattern_name = PatternType.N_QUEENS if "queen" in name_lower or "reina" in name_lower else PatternType.PERMUTATIONS
            
            return PatternClassification(
                pattern=pattern_name,
                complexity=sol.complexity,
                confidence=confidence,
                explanation="Backtracking: explora múltiples ramas, poda inviable",
                characteristics=[
                    f"{info.call_count}+ llamadas recursivas",
                    "Explora árbol de decisiones",
                    "Poda de ramas inviables",
                    "Complejidad factorial o exponencial"
                ]
            )

        # -------------------------------------------------
        # CASO GENÉRICO
        # -------------------------------------------------
        return PatternClassification(
            pattern=PatternType.UNKNOWN,
            complexity=sol.complexity,
            confidence=0.6,
            explanation=f"Patrón no reconocido. Complejidad estimada: {sol.complexity}",
            characteristics=[
                f"Tipo: {info.recursion_type}",
                f"Patrón: {info.depth_pattern}",
                f"{info.call_count} llamadas recursivas",
                f"Subproblema: {info.subproblem}"
            ]
        )

    def print_classification(self, classification: PatternClassification, func_name: str):
        """Imprime la clasificación de forma elegante"""
        print(f"\n╔{'═'*70}╗")
        print(f"║ 🎯 PATRÓN DETECTADO: {func_name:<48} ║")
        print(f"╠{'═'*70}╣")
        print(f"║ Algoritmo:    {classification.pattern.value:<53} ║")
        print(f"║ Complejidad:  {classification.complexity:<53} ║")
        print(f"║ Confianza:    {classification.confidence:.1%}{' '*52} ║")
        print(f"╠{'═'*70}╣")
        print(f"║ Explicación:                                                       ║")
        
        # Dividir explicación en líneas
        words = classification.explanation.split()
        line = "║ "
        for word in words:
            if len(line) + len(word) + 1 <= 69:
                line += word + " "
            else:
                print(f"{line:<71}║")
                line = "║ " + word + " "
        if len(line) > 3:
            print(f"{line:<71}║")
        
        # Características
        if classification.characteristics:
            print(f"╠{'═'*70}╣")
            print(f"║ Características:                                                   ║")
            for char in classification.characteristics:
                print(f"║   • {char:<65}║")
        
        print(f"╚{'═'*70}╝")