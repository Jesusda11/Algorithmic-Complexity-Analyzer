"""
Analizador de Complejidad Computacional (Actualizado)
Soporta recursión, ciclos anidados y procedimientos
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import sympy as sp


@dataclass
class Complexity:
    """Representa la complejidad de un algoritmo"""
    big_o: str       # Peor caso - O(n)
    omega: str       # Mejor caso - Ω(1)
    theta: str       # Caso promedio - Θ(n log n)
    explanation: str # Explicación del análisis
    steps: List[str] # Pasos del análisis
    
    def __str__(self):
        return f"O({self.big_o}), Ω({self.omega}), Θ({self.theta})"


class ComplexityAnalyzer:
    """
    Analizador de complejidad que recorre el AST y determina
    las complejidades temporal y espacial
    """
    
    def __init__(self, ast, recursion_info=None):
        self.ast = ast
        self.recursion_info = recursion_info or {}
        self.symbol_table = {}
        self.procedures = {}
        self.steps = []
        
        # Símbolos para análisis matemático
        self.n = sp.Symbol('n', positive=True, integer=True)
        self.m = sp.Symbol('m', positive=True, integer=True)
        
    def analyze(self) -> Complexity:
        """Punto de entrada principal del análisis"""
        self.steps.append("=== INICIO DEL ANÁLISIS DE COMPLEJIDAD ===\n")
        
        # 1. Registrar procedimientos
        self._register_procedures()
        
        # 2. Analizar recursión si existe
        self._analyze_recursion()
        
        # 3. Analizar cuerpo principal
        body_complexity = self._analyze_statements(self.ast["body"])
        
        # 4. Determinar complejidades finales
        big_o = self._simplify_complexity(body_complexity["worst"])
        omega = self._simplify_complexity(body_complexity["best"])
        theta = self._simplify_complexity(body_complexity["average"])
        
        explanation = self._generate_explanation(body_complexity)
        
        return Complexity(
            big_o=str(big_o),
            omega=str(omega),
            theta=str(theta),
            explanation=explanation,
            steps=self.steps
        )
    
    def _register_procedures(self):
        """Registra todos los procedimientos"""
        if "procedures" not in self.ast:
            return
        
        self.steps.append("--- Procedimientos encontrados ---")
        for proc in self.ast["procedures"]:
            name = proc["name"]
            self.procedures[name] = proc
            
            # Verificar si es recursivo
            is_recursive = (self.recursion_info.get(name) and 
                          self.recursion_info[name].is_recursive)
            
            if is_recursive:
                rec_info = self.recursion_info[name]
                self.steps.append(
                    f"  • {name}: RECURSIVO ({rec_info.recursion_type}, "
                    f"patrón: {rec_info.depth_pattern})"
                )
            else:
                self.steps.append(f"  • {name}: iterativo")
        
        self.steps.append("")
    
    def _analyze_recursion(self):
        """Analiza la complejidad de procedimientos recursivos"""
        if not self.recursion_info:
            return
        
        self.steps.append("--- Análisis de recursión ---")
        
        for proc_name, rec_info in self.recursion_info.items():
            if not rec_info.is_recursive:
                continue
            
            complexity = self._get_recursive_complexity(proc_name, rec_info)
            self.steps.append(
                f"\n  📌 {proc_name}:\n"
                f"     Tipo: {rec_info.recursion_type}\n"
                f"     Patrón: {rec_info.depth_pattern}\n"
                f"     Complejidad estimada: {complexity}"
            )
        
        self.steps.append("")
    
    def _get_recursive_complexity(self, proc_name, rec_info) -> str:
        """
        Estima la complejidad de un procedimiento recursivo
        basándose en su patrón
        """
        pattern = rec_info.depth_pattern
        
        if pattern == 'linear':
            # T(n) = T(n-1) + O(1) → O(n)
            return "O(n) - Recursión lineal"
        
        elif pattern == 'tree':
            # T(n) = 2*T(n-1) + O(1) → O(2^n)
            # o T(n) = 2*T(n/2) + O(n) → O(n log n)
            # Por ahora asumimos exponencial
            return "O(2^n) - Árbol de recursión"
        
        else:
            return "O(?) - Patrón desconocido"
    
    def _analyze_statements(self, statements) -> Dict:
        """Analiza una lista de statements secuenciales"""
        if not statements:
            return {"worst": 1, "best": 1, "average": 1}
        
        # Para statements secuenciales:
        # - Si son todas O(1), sumar
        # - Si hay alguna O(n) o mayor, tomar la dominante
        
        worst_list = []
        best_list = []
        average_list = []
        
        for stmt in statements:
            complexity = self._analyze_statement(stmt)
            worst_list.append(complexity["worst"])
            best_list.append(complexity["best"])
            average_list.append(complexity["average"])
        
        # Encontrar la complejidad dominante (la mayor)
        return {
            "worst": self._get_dominant_complexity(worst_list),
            "best": self._get_dominant_complexity(best_list),
            "average": self._get_dominant_complexity(average_list)
        }

    def _get_dominant_complexity(self, complexities):
        """
        Encuentra la complejidad dominante en una lista
        Si todas son constantes, suma. Si hay no constantes, toma la mayor.
        """
        # Filtrar constantes
        non_constants = [c for c in complexities if not (isinstance(c, (int, float)) and c <= 1)]
        
        if not non_constants:
            # Todas son O(1), sumar
            return sum(complexities)
        
        # Hay complejidades no constantes, retornar la mayor
        # Para símbolos, asumir que n > n-1 > ... > 1
        if len(non_constants) == 1:
            return non_constants[0]
        
        # Si hay múltiples, intentar comparar
        try:
            return max(non_constants, key=lambda x: sp.count_ops(x) if hasattr(x, 'count_ops') else 0)
        except:
            return non_constants[0]

    
    def _analyze_statement(self, stmt) -> Dict:
        """Analiza un statement individual"""
        stmt_type = stmt.get("type")
        
        if stmt_type == "block":
            return self._analyze_statements(stmt["body"])
        
        elif stmt_type == "for":
            return self._analyze_for(stmt)
        
        elif stmt_type == "while":
            return self._analyze_while(stmt)
        
        elif stmt_type == "repeat":
            return self._analyze_repeat(stmt)
        
        elif stmt_type == "if":
            return self._analyze_if(stmt)
        
        elif stmt_type == "call":
            return self._analyze_call(stmt)
        
        elif stmt_type in ("assign", "var_decl", "array_decl", "object_decl"):
            return {"worst": 1, "best": 1, "average": 1}
        
        else:
            return {"worst": 1, "best": 1, "average": 1}
    
    def _analyze_for(self, stmt) -> Dict:
        """Analiza ciclos FOR"""
        var = stmt["var"]
        start = stmt["start"]
        end = stmt["end"]
        body = stmt["body"]
        
        # Calcular iteraciones
        iterations = self._calculate_iterations(start, end)
        
        # Analizar cuerpo
        body_complexity = self._analyze_statement(body)
        
        # Complejidad total
        result = {
            "worst": iterations * body_complexity["worst"],
            "best": iterations * body_complexity["best"],
            "average": iterations * body_complexity["average"]
        }
        
        self.steps.append(
            f"\n  FOR {var} = {self._expr_to_str(start)} to {self._expr_to_str(end)}:\n"
            f"    Iteraciones: {iterations}\n"
            f"    Cuerpo: O({body_complexity['worst']})\n"
            f"    Total: O({self._simplify_complexity(result['worst'])})"
        )
        
        return result
    
    def _analyze_while(self, stmt) -> Dict:
        """Analiza ciclos WHILE"""
        body = stmt["body"]
        body_complexity = self._analyze_statement(body)
        
        iterations = self.n
        
        result = {
            "worst": iterations * body_complexity["worst"],
            "best": 1,
            "average": iterations * body_complexity["average"]
        }
        
        self.steps.append(
            f"\n  WHILE (condición):\n"
            f"    Iteraciones asumidas: {iterations}\n"
            f"    Total: O({self._simplify_complexity(result['worst'])})"
        )
        
        return result
    
    def _analyze_repeat(self, stmt) -> Dict:
        """Analiza ciclos REPEAT-UNTIL"""
        body = stmt["body"]
        body_complexity = self._analyze_statements(body)
        
        iterations = self.n
        
        result = {
            "worst": iterations * body_complexity["worst"],
            "best": 1,
            "average": iterations * body_complexity["average"]
        }
        
        self.steps.append(
            f"\n  REPEAT-UNTIL:\n"
            f"    Iteraciones: {iterations}\n"
            f"    Total: O({self._simplify_complexity(result['worst'])})"
        )
        
        return result
    
    def _analyze_if(self, stmt) -> Dict:
        """Analiza condicionales IF"""
        then_complexity = self._analyze_statement(stmt["then"])
        else_complexity = self._analyze_statement(stmt["else"])
        
        result = {
            "worst": sp.Max(then_complexity["worst"], else_complexity["worst"]),
            "best": sp.Min(then_complexity["best"], else_complexity["best"]),
            "average": (then_complexity["average"] + else_complexity["average"]) / 2
        }
        
        self.steps.append(
            f"\n  IF-THEN-ELSE:\n"
            f"    THEN: O({then_complexity['worst']})\n"
            f"    ELSE: O({else_complexity['worst']})\n"
            f"    Peor caso: O({self._simplify_complexity(result['worst'])})"
        )
        
        return result
    
    def _analyze_call(self, stmt) -> Dict:
        """Analiza llamadas a procedimientos"""
        proc_name = stmt["name"]
        
        # Verificar si es recursivo
        if proc_name in self.recursion_info and self.recursion_info[proc_name].is_recursive:
            rec_info = self.recursion_info[proc_name]
            
            if rec_info.depth_pattern == 'linear':
                complexity_value = self.n
            elif rec_info.depth_pattern == 'tree':
                complexity_value = 2**self.n
            else:
                complexity_value = self.n
            
            self.steps.append(
                f"\n  CALL {proc_name}() [RECURSIVO]:\n"
                f"    Complejidad: O({complexity_value})"
            )
            
            return {"worst": complexity_value, "best": complexity_value, "average": complexity_value}
        
        # Si no es recursivo, analizar su cuerpo
        if proc_name in self.procedures:
            proc = self.procedures[proc_name]
            body_complexity = self._analyze_statement(proc["body"])
            
            self.steps.append(
                f"\n  CALL {proc_name}():\n"
                f"    Complejidad: O({body_complexity['worst']})"
            )
            
            return body_complexity
        else:
            # Procedimiento desconocido
            self.steps.append(f"\n  CALL {proc_name}(): O(1) [desconocido]")
            return {"worst": 1, "best": 1, "average": 1}
    
    def _calculate_iterations(self, start, end):
        """Calcula iteraciones de un FOR"""
        if isinstance(end, dict) and end.get("type") == "length":
            return self.n
        
        if (isinstance(start, dict) and start.get("type") == "number" and
            isinstance(end, dict) and end.get("type") == "number"):
            return end["value"] - start["value"] + 1
        
        # Caso con variables
        if isinstance(end, dict) and end.get("type") == "var":
            return self.n
        
        return self.n
    
    def _expr_to_str(self, expr):
        """Convierte una expresión AST a string"""
        if isinstance(expr, dict):
            if expr.get("type") == "number":
                return str(expr["value"])
            elif expr.get("type") == "var":
                return expr["value"]
            elif expr.get("type") == "length":
                return "length(...)"
        return "expr"
    
    def _simplify_complexity(self, expr):
        """Simplifica una expresión a su forma Big-O"""
        if isinstance(expr, (int, float)):
            return 1 if expr <= 1 else expr
        
        try:
            simplified = sp.simplify(expr)
            
            if isinstance(simplified, sp.Add):
                terms = simplified.as_ordered_terms()
                dominant = terms[-1]
                return dominant
            
            return simplified
        except:
            return expr
    
    def _generate_explanation(self, complexity) -> str:
        """Genera explicación del análisis"""
        explanation = "ANÁLISIS DE COMPLEJIDAD:\n\n"
        
        for step in self.steps:
            explanation += step + "\n"
        
        explanation += f"\n=== RESULTADO FINAL ===\n"
        explanation += f"Peor caso (Big-O):     O({self._simplify_complexity(complexity['worst'])})\n"
        explanation += f"Mejor caso (Omega):    Ω({self._simplify_complexity(complexity['best'])})\n"
        explanation += f"Caso promedio (Theta): Θ({self._simplify_complexity(complexity['average'])})\n"
        
        return explanation