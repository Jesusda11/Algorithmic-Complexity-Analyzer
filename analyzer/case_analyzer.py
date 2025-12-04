# analyzer/case_analyzer.py
"""
Analizador de Mejor y Peor Caso
Detecta diferencias en complejidad según el comportamiento del algoritmo
"""

from typing import Dict, Any
import sympy as sp

class CaseAnalyzer:
    """
    Analiza mejor y peor caso detectando:
    1. Early exits (salidas tempranas de ciclos)
    2. Condiciones que afectan número de iteraciones
    3. Recursión con casos base diferentes
    """
    
    def __init__(self):
        self.n = sp.Symbol('n', positive=True, integer=True)
        self.has_early_exit = False
        self.analysis_notes = []
    
    def analyze_loop_cases(self, loop_node: Dict) -> Dict[str, Any]:
        """
        Analiza mejor y peor caso de un ciclo
        
        Args:
            loop_node: Nodo del AST representando un ciclo (for, while, repeat)
        
        Returns:
            Dict con complejidades de mejor/peor caso y explicación
        """
        loop_type = loop_node.get("type")
        
        if loop_type == "for":
            return self._analyze_for_cases(loop_node)
        elif loop_type == "while":
            return self._analyze_while_cases(loop_node)
        elif loop_type == "repeat":
            return self._analyze_repeat_cases(loop_node)
        
        # Por defecto, sin diferencia
        return {
            "worst": self.n,
            "best": self.n,
            "average": self.n,
            "differs": False,
            "explanation": "No se detectaron diferencias entre casos"
        }
    
    def _analyze_for_cases(self, for_node: Dict) -> Dict[str, Any]:
        """
        Analiza ciclo FOR
        
        Casos donde difiere:
        1. Hay un IF con return/break/flag que termina el ciclo
        2. Hay una llamada que podría terminar el ciclo
        """
        body = for_node["body"]
        
        # Calcular iteraciones máximas
        start = for_node["start"]
        end = for_node["end"]
        max_iterations = self._calculate_max_iterations(start, end)
        
        # Buscar condiciones de salida temprana
        has_early_exit = self._has_early_exit(body)
        
        if has_early_exit:
            self.analysis_notes.append(
                f"⚠️ FOR con posible salida temprana detectada"
            )
            
            return {
                "worst": max_iterations,
                "best": 1,  # Mejor caso: sale en primera iteración
                "average": max_iterations / 2,  # Caso promedio: mitad de iteraciones
                "differs": True,
                "explanation": (
                    "El ciclo tiene condiciones que pueden terminarlo tempranamente.\n"
                )
            }
        
        # Sin salida temprana, todos los casos son iguales
        return {
            "worst": max_iterations,
            "best": max_iterations,
            "average": max_iterations,
            "differs": False,
            "explanation": f"El ciclo siempre itera {max_iterations} veces"
        }
    
    def _analyze_while_cases(self, while_node: Dict) -> Dict[str, Any]:
        """
        Analiza ciclo WHILE
        
        WHILE es más difícil de analizar porque depende de la condición
        """
        condition = while_node["cond"]
        body = while_node["body"]
        
        # Heurística: si hay comparación con elemento, podría ser búsqueda
        if self._is_search_pattern(condition, body):
            self.analysis_notes.append(
                "⚠️ WHILE con patrón de búsqueda detectado"
            )
            
            return {
                "worst": self.n,
                "best": 1,
                "average": self.n / 2,
                "differs": True,
                "explanation": (
                    "WHILE con patrón de búsqueda:\n"
                    "  - Peor caso: O(n) - recorre todo\n"
                    "  - Mejor caso: O(1) - encuentra inmediatamente\n"
                    "  - Caso promedio: O(n/2) ≈ O(n)"
                )
            }
        
        # Por defecto, asumir n iteraciones
        return {
            "worst": self.n,
            "best": self.n,
            "average": self.n,
            "differs": False,
            "explanation": "WHILE: número de iteraciones depende de la condición (asumido n)"
        }
    
    def _analyze_repeat_cases(self, repeat_node: Dict) -> Dict[str, Any]:
        """
        Analiza ciclo REPEAT-UNTIL
        
        Se ejecuta al menos una vez, luego depende de la condición
        """
        return {
            "worst": self.n,
            "best": 1,  # Al menos una iteración
            "average": self.n / 2,
            "differs": True,
            "explanation": (
                "REPEAT-UNTIL:\n"
                "  - Peor caso: O(n)\n"
                "  - Mejor caso: O(1) - condición se cumple en primera iteración\n"
                "  - Caso promedio: O(n/2) ≈ O(n)"
            )
        }
    
    def _calculate_max_iterations(self, start, end):
        """Calcula el máximo de iteraciones de un FOR"""
        # Si end es length(A), retornar n
        if isinstance(end, dict) and end.get("type") == "length":
            return self.n
        
        # Si end es una variable, asumir n
        if isinstance(end, dict) and end.get("type") == "var":
            return self.n
        
        # Si son números constantes
        if (isinstance(start, dict) and start.get("type") == "number" and
            isinstance(end, dict) and end.get("type") == "number"):
            return end["value"] - start["value"] + 1
        
        # Por defecto, n
        return self.n
    
    def _has_early_exit(self, body_node) -> bool:
        """
        Detecta si hay posibilidad de salida temprana del ciclo
        
        Busca:
        1. IF con asignación a flag/variable de control
        2. IF con break/return (si lo soportas)
        3. Modificación de variable de control dentro del ciclo
        """
        if not isinstance(body_node, dict):
            return False
        
        # Explorar el body recursivamente
        return self._search_early_exit_pattern(body_node)
    
    def _search_early_exit_pattern(self, node, depth=0) -> bool:
        """
        Búsqueda recursiva de patrones de salida temprana
        
        Patrones que indican early exit:
        1. IF con asignación a una variable booleana/flag
        2. IF con modificación de variable de control del ciclo
        """
        if depth > 10:  # Evitar recursión infinita
            return False
        
        if isinstance(node, dict):
            node_type = node.get("type")
            
            # Patrón 1: IF con asignación en el THEN
            if node_type == "if":
                then_branch = node.get("then", {})
                
                # Buscar asignaciones de flags booleanos
                if self._has_flag_assignment(then_branch):
                    return True
                
                # Buscar modificación de índice/contador
                if self._has_counter_modification(then_branch):
                    return True
            
            # Buscar recursivamente en hijos
            for value in node.values():
                if isinstance(value, (dict, list)):
                    if self._search_early_exit_pattern(value, depth + 1):
                        return True
        
        elif isinstance(node, list):
            for item in node:
                if self._search_early_exit_pattern(item, depth + 1):
                    return True
        
        return False
    
    def _has_flag_assignment(self, node) -> bool:
        """Detecta asignación de flags booleanos"""
        if isinstance(node, dict):
            if node.get("type") == "assign":
                expr = node.get("expr", {})
                target = node.get("target", {})
                
                # Si asigna un booleano
                if expr.get("type") == "boolean":
                    return True
                
                # AÑADIR: Si asigna T o F como variable (workaround)
                if expr.get("type") == "var" and expr.get("value") in ("T", "F"):
                    return True
                
                # AÑADIR: Si el nombre de la variable sugiere un flag
                if target.get("type") == "var":
                    target_name = target.get("value", "").lower()
                    if any(flag in target_name for flag in ["encontrado", "found", "done", "flag", "terminar"]):
                        return True
            
            # Buscar en block
            if node.get("type") == "block":
                for stmt in node.get("body", []):
                    if self._has_flag_assignment(stmt):
                        return True
        
        return False
    
    def _has_counter_modification(self, node) -> bool:
        """
        Detecta modificación de variable de control
        Ejemplo: i 🡨 n + 1 (fuerza salida del ciclo)
        """
        if isinstance(node, dict):
            if node.get("type") == "assign":
                target = node.get("target", {})
                expr = node.get("expr", {})
                
                # Si asigna un valor grande a i/j/contador
                if target.get("type") == "var":
                    var_name = target.get("value", "")
                    # Variables típicas de control de ciclos
                    if var_name in ("i", "j", "k", "idx", "pos"):
                        return True
            
            # Buscar en block
            if node.get("type") == "block":
                for stmt in node.get("body", []):
                    if self._has_counter_modification(stmt):
                        return True
        
        return False
    
    def _is_search_pattern(self, condition, body) -> bool:
        """
        Detecta si es un patrón de búsqueda
        
        Indicadores:
        1. Condición compara con un objetivo
        2. Body tiene un IF que compara elementos
        """
        # Heurística simple: si el body tiene un IF con comparación
        if isinstance(body, dict) and body.get("type") == "block":
            for stmt in body.get("body", []):
                if stmt.get("type") == "if":
                    # Probablemente es una búsqueda
                    return True
        
        return False
    
    def analyze_recursive_cases(self, proc_name: str, proc_body: Dict, 
                                recursion_info) -> Dict[str, Any]:
        """
        Analiza mejor/peor caso de procedimientos recursivos
        
        Factores que afectan:
        1. Casos base diferentes
        2. Número de llamadas recursivas
        3. Tamaño de la reducción del problema
        """
        if not recursion_info.get(proc_name) or not recursion_info[proc_name].is_recursive:
            # No es recursivo
            return {
                "worst": 1,
                "best": 1,
                "average": 1,
                "differs": False
            }
        
        rec_info = recursion_info[proc_name]
        
        # Análisis según patrón
        if rec_info.depth_pattern == 'linear':
            # T(n) = T(n-1) + O(1)
            return {
                "worst": self.n,
                "best": self.n,  # Todos los casos son lineales
                "average": self.n,
                "differs": False,
                "explanation": "Recursión lineal: O(n) en todos los casos"
            }
        
        elif rec_info.depth_pattern == 'tree':
            # T(n) = 2*T(n-1) + O(1) o similar
            # Fibonacci: todos los casos son O(2^n)
            return {
                "worst": 2**self.n,
                "best": 2**self.n,
                "average": 2**self.n,
                "differs": False,
                "explanation": "Árbol de recursión: O(2^n) en todos los casos"
            }
        
        return {
            "worst": self.n,
            "best": self.n,
            "average": self.n,
            "differs": False
        }


# ========================================
# INTEGRACIÓN CON ComplexityAnalyzer
# ========================================

def enhance_complexity_analyzer():
    """
    Código para integrar CaseAnalyzer con tu ComplexityAnalyzer existente
    """
    
    # En tu ComplexityAnalyzer.__init__:
    # self.case_analyzer = CaseAnalyzer()
    
    # En tu _analyze_for, reemplazar:
    """
    def _analyze_for(self, stmt) -> Dict:
        # ... código existente ...
        
        # AÑADIR: Analizar casos
        case_analysis = self.case_analyzer.analyze_loop_cases(stmt)
        
        if case_analysis["differs"]:
            # Los casos difieren
            result = {
                "worst": case_analysis["worst"] * body_complexity["worst"],
                "best": case_analysis["best"] * body_complexity["best"],
                "average": case_analysis["average"] * body_complexity["average"]
            }
            
            self.steps.append(
                f"\\nFOR con diferencias entre casos:\\n"
                f"{case_analysis['explanation']}\\n"
                f"  Complejidad cuerpo: O({body_complexity['worst']})\\n"
                f"  Total peor caso: O({result['worst']})\\n"
                f"  Total mejor caso: O({result['best']})"
            )
        else:
            # Código original para cuando no difieren
            ...
        
        return result
    """


# ========================================
# TESTS
# ========================================

def test_search_with_early_exit():
    """Test: Búsqueda lineal con salida temprana"""
    
    # Simular AST de búsqueda lineal
    for_node = {
        "type": "for",
        "var": "i",
        "start": {"type": "number", "value": 1},
        "end": {"type": "var", "value": "n"},
        "body": {
            "type": "block",
            "body": [
                {
                    "type": "if",
                    "cond": {
                        "type": "binop",
                        "op": "EQ",
                        "left": {"type": "array_access", "array": {"type": "var", "value": "A"}},
                        "right": {"type": "var", "value": "objetivo"}
                    },
                    "then": {
                        "type": "block",
                        "body": [
                            {
                                "type": "assign",
                                "target": {"type": "var", "value": "encontrado"},
                                "expr": {"type": "boolean", "value": True}
                            }
                        ]
                    },
                    "else": {
                        "type": "block",
                        "body": []
                    }
                }
            ]
        }
    }
    
    analyzer = CaseAnalyzer()
    result = analyzer.analyze_loop_cases(for_node)
    
    print("=" * 70)
    print("TEST: Búsqueda Lineal con Early Exit")
    print("=" * 70)
    print(f"Mejor caso: {result['best']}")
    print(f"Peor caso: {result['worst']}")
    print(f"Caso promedio: {result['average']}")
    print(f"¿Difieren los casos? {result['differs']}")
    print(f"\nExplicación:\n{result['explanation']}")
    
    assert result['differs'] == True
    assert result['best'] == 1
    print("\n✅ Test pasado!")


if __name__ == "__main__":
    test_search_with_early_exit()