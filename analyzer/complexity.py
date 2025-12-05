from .case_analyzer import CaseAnalyzer
from .recurrence import RecurrenceSolver, RecurrenceRelation

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
    recurrence_info: Optional[Dict] = None
    per_procedure_analysis: Optional[Dict] = None   # ← AÑADE ESTO

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
        self.case_analyzer = CaseAnalyzer()

        self.per_procedure_analysis = {}
        
        # ← NUEVO: Solver de recurrencias
        self.recurrence_solver = RecurrenceSolver()
        self.recurrence_solutions = {}  # Guardar soluciones
        
        # Símbolos para análisis matemático
        self.n = sp.Symbol('n', positive=True, integer=True)
        self.m = sp.Symbol('m', positive=True, integer=True)
        
    def analyze(self) -> Complexity:
        """Punto de entrada principal del análisis"""
        self.steps.append("=== INICIO DEL ANÁLISIS DE COMPLEJIDAD ===\n")
        
        # 1. Registrar procedimientos
        self._register_procedures()
        
        # 2. Analizar recursión si existe (usando RecurrenceSolver)
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
            steps=self.steps,
            recurrence_info=self.recurrence_solutions,  # ← NUEVO
            per_procedure_analysis=self.per_procedure_analysis
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
        """Analiza la complejidad de procedimientos recursivos usando RecurrenceSolver"""
        if not self.recursion_info:
            return

        self.steps.append("--- Análisis de recursión ---")

        for proc_name, rec_info in self.recursion_info.items():
            if not rec_info.is_recursive:
                continue

            proc_ast = self.procedures.get(proc_name)

            # Intento 1: inferir directamente desde AST
            recurrence_relation = None
            if proc_ast:
                recurrence_relation = self.recurrence_solver.infer_from_ast(
                    proc_name,
                    proc_ast,
                    self.recursion_info,
                    self.procedures
                )

            # Intento 2: construir heurísticamente
            if recurrence_relation is None:
                recurrence_relation = self._build_recurrence_from_recinfo(proc_name, rec_info)

            if recurrence_relation:
                solution = self.recurrence_solver.solve(recurrence_relation)

                # ✅ GUARDAR PARA EL CLASIFICADOR DE PATRONES
                self.per_procedure_analysis[proc_name] = {
                    "recursion_info": rec_info,
                    "relation": recurrence_relation,
                    "solution": solution,
                    "complexity": solution.complexity,
                    "method": solution.method
                }

                # Compatibilidad con el sistema anterior
                self.recurrence_solutions[proc_name] = {
                    'relation': str(recurrence_relation),
                    'solution': solution.complexity,
                    'method': solution.method,
                    'explanation': solution.explanation
                }

                # Mostrar en pasos
                self.steps.append(
                    f"\n  {proc_name}:\n"
                    f"     Relación de recurrencia: {recurrence_relation}\n"
                    f"     Solución: {solution.complexity}\n"
                    f"     Método: {solution.method}\n"
                    f"\n     Explicación detallada:\n"
                )
                for line in solution.explanation.split('\n'):
                    if line.strip():
                        self.steps.append(f"     {line}")
                self.steps.append("")

            else:
                complexity_estimate = self._get_recursive_complexity(proc_name, rec_info)
                
                # Crear un objeto "solution" simulado para mantener consistencia
                class FallbackSolution:
                    def __init__(self, complexity_str):
                        self.complexity = complexity_str
                        self.method = "Estimación heurística"
                        self.explanation = f"No se pudo construir relación de recurrencia precisa. Estimación basada en patrón: {rec_info.depth_pattern}"
                
                fallback_solution = FallbackSolution(complexity_estimate)
                
                # ✅ LLENAR per_procedure_analysis INCLUSO SIN RELACIÓN
                self.per_procedure_analysis[proc_name] = {
                    "recursion_info": rec_info,
                    "relation": None,  # No hay relación formal
                    "solution": fallback_solution,
                    "complexity": complexity_estimate,
                    "method": "Heurística"
                }
                
                self.steps.append(
                    f"\n  {proc_name}:\n"
                    f"     Tipo: {rec_info.recursion_type}\n"
                    f"     Patrón: {rec_info.depth_pattern}\n"
                    f"     Complejidad estimada: {complexity_estimate}\n"
                    f"     ⚠️ (No se pudo construir relación de recurrencia precisa)"
                )

        self.steps.append("")

    def _get_recursive_complexity(self, proc_name, rec_info) -> str:
        """
        Estima la complejidad de un procedimiento recursivo
        basándose en su patrón (método de respaldo si RecurrenceSolver falla)
        
        VERSIÓN MEJORADA con mejor formato
        """
        pattern = rec_info.depth_pattern
        
        if pattern == 'linear':
            return "O(n)"
        
        elif pattern == 'divide_and_conquer':
            # Si divide en n/2
            if rec_info.subproblem == "n/2":
                if rec_info.call_count == 1:
                    return "O(log n)"  # Binary search-like
                elif rec_info.call_count == 2:
                    if rec_info.has_combining_work:
                        return "O(n log n)"  # Merge sort-like
                    else:
                        return "O(n log n)"  # Divide and conquer típico
            return "O(n log n)"  # Estimación conservadora
        
        elif pattern == 'tree':
            if rec_info.call_count == 2:
                return "O(2^n)"  # Fibonacci-like
            else:
                return f"O({rec_info.call_count}^n)"
        
        else:
            return "O(n)"

    def _build_recurrence_from_recinfo(self, proc_name, rec_info):
        """
        Construye heurísticamente una RecurrenceRelation a partir de RecursionInfo.
        Returns RecurrenceRelation or None
        """
        # Necesitamos RecurrenceRelation importada: RecurrenceRelation(a, b, f_complexity, reduction_type)
        try:
            a = max(1, rec_info.call_count)  # número de llamadas activas (heurística)
            sub = getattr(rec_info, "subproblem", "unknown")
            has_combine = getattr(rec_info, "has_combining_work", False)

            # Si sabemos que divide en n/2
            if sub == "n/2":
                b = 2
                reduction_type = "divide"
            elif sub and sub.startswith("n/"):
                # n/k -> extraer k
                try:
                    k = int(sub.split("/")[1])
                    b = k
                    reduction_type = "divide"
                except:
                    b = 2
                    reduction_type = "divide"
            elif sub == "n-1":
                b = 1
                reduction_type = "subtract"
            elif sub == "slice":
                # slice ≈ divide, asumimos n/2
                b = 2
                reduction_type = "divide"
            else:
                # unknown -> no podemos construir bien
                return None

            # Estimación del trabajo no recursivo f(n)
            # Si hay trabajo de combinación (merge/partition), asumimos O(n); si no, O(1)
            f_complexity = "n" if has_combine else "1"

            return RecurrenceRelation(a=a, b=b, f_complexity=f_complexity, reduction_type=reduction_type)
        except Exception:
            return None


    
    def _get_recursive_complexity(self, proc_name, rec_info) -> str:
        """
        Estima la complejidad de un procedimiento recursivo
        basándose en su patrón (método de respaldo si RecurrenceSolver falla)
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
        non_constants = [c for c in complexities if not (isinstance(c, (int, float)) and c <= 1)]
        if not non_constants:
            return sum(complexities)
        
        # Si hay sumas de complejidades, intentamos simplificar
        try:
            # Sumar todas y dejar que sympy simplifique al dominante
            total = sum(non_constants)
            return sp.simplify(total)
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
        
        # ✅ NUEVO: Manejar call_expr
        elif stmt_type == "call_expr":
            return self._analyze_call(stmt)

        elif stmt_type == "return":
            if stmt.get("expr"):
                return self._analyze_expression_complexity(stmt["expr"])
            return {"worst": 1, "best": 1, "average": 1}
        
        elif stmt_type in ("assign", "var_decl", "array_decl", "object_decl"):
            # ✅ MODIFICADO: Analizar expresión de asignaciones
            if stmt_type == "assign":
                expr = stmt.get("expr", {})
                return self._analyze_expression_complexity(expr)
            return {"worst": 1, "best": 1, "average": 1}
        
        else:
            return {"worst": 1, "best": 1, "average": 1}
    
    def _analyze_for(self, stmt) -> Dict:
        """Analiza ciclos FOR"""
        var = stmt["var"]
        start = stmt["start"]
        end = stmt["end"]
        body = stmt["body"]
        
        iterations = self._calculate_iterations(start, end)

        body_complexity = self._analyze_statement(body)
        
        case_analysis = self.case_analyzer.analyze_loop_cases(stmt)
        
        if case_analysis["differs"]:
            # Los casos difieren
            result = {
                "worst": case_analysis["worst"] * body_complexity["worst"],
                "best": case_analysis["best"] * body_complexity["best"],
                "average": case_analysis["average"] * body_complexity["average"]
            }
            
            self.steps.append(
                f"\n  FOR {var} con EARLY EXIT detectado:\n"
                f"    {case_analysis['explanation']}\n"
                f"    Cuerpo: O({body_complexity['worst']})\n"
                f"    Peor caso total: O({self._simplify_complexity(result['worst'])})\n"
                f"    Mejor caso total: O({self._simplify_complexity(result['best'])})"
            )
        else:
            # Sin early exit - todos los casos iguales
            iterations = self._calculate_iterations(start, end)
            
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
            """Analiza ciclos WHILE detectando patrones de paso (logarítmico vs lineal)"""
            body = stmt["body"]
            cond = stmt["cond"]
            
            # 1. Analizar complejidad del cuerpo
            body_complexity = self._analyze_statement(body)
            
            # 2. Inferir número de iteraciones basado en la condición y el cuerpo
            iter_info = self._infer_loop_complexity(cond, body)
            iterations = iter_info["iterations"]
            pattern_type = iter_info["pattern"]
            
            # 3. Calcular total
            result = {
                "worst": iterations * body_complexity["worst"],
                "best": 1, # En el mejor caso la condición es falsa al inicio
                "average": iterations * body_complexity["average"]
            }
            
            self.steps.append(
                f"\n  WHILE ({self._expr_to_str(cond)}):\n"
                f"    Patrón detectado: {pattern_type}\n"
                f"    Iteraciones estimadas: O({self._simplify_complexity(iterations)})\n"
                f"    Cuerpo: O({self._simplify_complexity(body_complexity['worst'])})\n"
                f"    Total Peor Caso: O({self._simplify_complexity(result['worst'])})"
            )
        
            return result
    
    def _analyze_repeat(self, stmt) -> Dict:
        """Analiza ciclos REPEAT-UNTIL"""
        body = stmt["body"]
        cond = stmt["cond"] # until condition
        
        body_complexity = self._analyze_statements(body)
        
        # Reutilizamos la lógica de inferencia (similar al while pero se ejecuta al menos 1 vez)
        iter_info = self._infer_loop_complexity(cond, body)
        iterations = iter_info["iterations"]
        pattern_type = iter_info["pattern"]
        
        result = {
            "worst": iterations * body_complexity["worst"],
            "best": body_complexity["best"], # Se ejecuta al menos una vez
            "average": iterations * body_complexity["average"]
        }
        
        self.steps.append(
            f"\n  REPEAT-UNTIL ({self._expr_to_str(cond)}):\n"
            f"    Patrón detectado: {pattern_type}\n"
            f"    Total Peor Caso: O({self._simplify_complexity(result['worst'])})"
        )
        
        return result
    
    def _infer_loop_complexity(self, condition, body) -> Dict:
        """
        Intenta deducir la complejidad del ciclo analizando la variable de control.
        Soporta: Linear O(n), Logarítmico O(log n), Raíz O(sqrt n)
        """
        default_result = {"iterations": self.n, "pattern": "Lineal Genérico (Asumido)"}
        
        # 1. Extraer variable de control de la condición (ej: 'i' de 'i < n')
        control_var = self._extract_control_var(condition)
        if not control_var:
            return default_result
            
        # 2. Buscar cómo se modifica esa variable en el cuerpo
        modification = self._find_variable_modification(body, control_var)
        if not modification:
            return default_result
            
        op = modification["op"]
        value = modification["value"] # El valor por el que se suma/multiplica
        
        # 3. Determinar complejidad según la operación
        if op in ("+", "-"):
            # i = i + k  -->  O(n)
            return {"iterations": self.n, "pattern": f"Lineal (Paso {op} const)"}
            
        elif op == "*":
            # i = i * k  -->  O(log_k n)
            # Si k es 2, es log2(n)
            if str(value) == "2":
                return {"iterations": sp.log(self.n, 2), "pattern": "Logarítmico (Multiplicación x2)"}
            else:
                return {"iterations": sp.log(self.n), "pattern": "Logarítmico (Multiplicación)"}
                
        elif op == "/":
            # i = i / k  -->  O(log_k n)
            return {"iterations": sp.log(self.n), "pattern": "Logarítmico (División)"}
            
        elif op == "^" or op == "**":
            # i = i^2 (si condición es i < n) --> O(log log n) 
            # i = i^2 (si update es rápido)
            return {"iterations": sp.log(sp.log(self.n)), "pattern": "Doble Logarítmico"}

        return default_result

    def _extract_control_var(self, condition):
        """Extrae el nombre de la variable principal de una condición simple"""
        if not isinstance(condition, dict): return None
        
        # Caso: i < n, i > 0, i != n
        if condition.get("type") == "binop":
            left = condition.get("left", {})
            right = condition.get("right", {})
            
            # Asumimos que la variable está a la izquierda (estándar) o derecha
            if left.get("type") == "var":
                return left["value"]
            elif right.get("type") == "var":
                return right["value"]
        return None

    def _find_variable_modification(self, body, var_name):
        """Busca en el cuerpo del ciclo cómo se modifica la variable var_name"""
        # Si es un bloque, buscar en la lista de instrucciones
        stmts = []
        if isinstance(body, dict) and body.get("type") == "block":
            stmts = body.get("body", [])
        elif isinstance(body, list):
            stmts = body
        else:
            stmts = [body]
            
        for stmt in stmts:
            if stmt.get("type") == "assign":
                target = stmt.get("target", {})
                if target.get("type") == "var" and target.get("value") == var_name:
                    return self._analyze_assignment_math(stmt["expr"], var_name)
            
            # Soporte para inc(i) o dec(i) si existen en tu lenguaje
            if stmt.get("type") == "call":
                if stmt.get("name") == "inc" and stmt["args"][0]["value"] == var_name:
                     return {"op": "+", "value": 1}
        return None

    def _analyze_assignment_math(self, expr, var_name):
        """
        Analiza: i = i + 1, i = i * 2, etc.
        Detecta el operador matemático real desde el token del parser.
        """
        # Tu AST dice "type": "binop", asegúrate de verificar eso
        if expr.get("type") == "binop" or expr.get("type") == "binary":
            op_token = expr["op"] # Aquí llega "PLUS", "MULT", etc.
            
            op_map = {
                "PLUS": "+",
                "MINUS": "-",
                "MULT": "*",
                "TIMES": "*",
                "STAR": "*",
                "DIV": "/",
                "MOD": "%"
            } 
            op = op_map.get(op_token, op_token) 
            # ================================

            left = expr.get("left", {})
            right = expr.get("right", {})
            
            # Chequear si es: i = i + K  o  i = K + i
            is_left_var = left.get("type") == "var" and left.get("value") == var_name
            is_right_var = right.get("type") == "var" and right.get("value") == var_name
            
            other_val = right if is_left_var else left
            
            # Solo nos interesa si la variable opera sobre sí misma
            if is_left_var or is_right_var:
                # Extraer el valor numérico o simbólico
                val_str = str(other_val.get("value", "k"))
                return {"op": op, "value": val_str}
                
        return None
    
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
        """
        Analiza llamadas a procedimientos
        🔧 ACTUALIZADO: Usa las soluciones del RecurrenceSolver correctamente
        """
        proc_name = stmt["name"]
        
        if proc_name in self.recurrence_solutions:
            solution = self.recurrence_solutions[proc_name]
            complexity_str = solution['solution']
            
            
            complexity_expr = complexity_str.replace("O(", "").replace(")", "").strip()
            
            complexity_value = self._parse_complexity_string(complexity_expr)
            
            self.steps.append(
                f"\n  CALL {proc_name}() [RECURSIVO - Solución exacta]:\n"
                f"    Relación: {solution['relation']}\n"
                f"    Complejidad: {complexity_str}\n"
                f"    Método: {solution['method']}"
            )
            
            return {
                "worst": complexity_value, 
                "best": complexity_value, 
                "average": complexity_value
            }
        
        if proc_name in self.recursion_info and self.recursion_info[proc_name].is_recursive:
            rec_info = self.recursion_info[proc_name]
            
            if rec_info.depth_pattern == 'linear':
                complexity_value = self.n
                explanation = "Recursión lineal (estimada)"
            elif rec_info.depth_pattern == 'tree':
                # Podría ser divide-and-conquer que no se resolvió
                complexity_value = self.n * sp.log(self.n)
                explanation = "Recursión tipo árbol (estimación conservadora)"
            else:
                complexity_value = self.n
                explanation = "Recursión desconocida (estimada)"
            
            self.steps.append(
                f"\n  CALL {proc_name}() [RECURSIVO - Sin resolver]:\n"
                f"    Tipo: {rec_info.recursion_type}\n"
                f"    Patrón: {rec_info.depth_pattern}\n"
                f"    Complejidad estimada: O({complexity_value})\n"
                f"    ⚠️ Advertencia: {explanation}"
            )
            
            return {
                "worst": complexity_value, 
                "best": complexity_value, 
                "average": complexity_value
            }
        
        if proc_name in self.procedures:
            proc = self.procedures[proc_name]
            body_complexity = self._analyze_statement(proc["body"])
            
            self.steps.append(
                f"\n  CALL {proc_name}() [ITERATIVO]:\n"
                f"    Complejidad: O({body_complexity['worst']})"
            )
            
            return body_complexity
        
        self.steps.append(
            f"\n  CALL {proc_name}() [DESCONOCIDO]:\n"
            f"    Asumiendo: O(1)"
        )
        return {"worst": 1, "best": 1, "average": 1}

    def _analyze_expression_complexity(self, expr) -> Dict:
        """
        Analiza la complejidad de una expresión
        (útil para returns, assigns, etc.)
        """
        if not isinstance(expr, dict):
            return {"worst": 1, "best": 1, "average": 1}
        
        expr_type = expr.get("type")
        
        # Llamadas a funciones dentro de expresiones
        if expr_type == "call" or expr_type == "call_expr":
            return self._analyze_call(expr)
        
        # Operaciones binarias: analizar ambos lados
        elif expr_type == "binop":
            left = self._analyze_expression_complexity(expr.get("left", {}))
            right = self._analyze_expression_complexity(expr.get("right", {}))
            
            return {
                "worst": sp.Max(left["worst"], right["worst"]),
                "best": sp.Max(left["best"], right["best"]),
                "average": sp.Max(left["average"], right["average"])
            }
        
        # Operaciones unarias
        elif expr_type == "unop":
            return self._analyze_expression_complexity(expr.get("operand", {}))
        
        # Acceso a arrays/índices
        elif expr_type == "index":
            index_expr = expr.get("index", {})
            return self._analyze_expression_complexity(index_expr)
        
        # Todo lo demás es O(1)
        else:
            return {"worst": 1, "best": 1, "average": 1}

    def _parse_complexity_string(self, complexity_str: str):
        """
        🆕 NUEVO MÉTODO: Convierte string de complejidad a expresión sympy
        
        Ejemplos:
        - "log(n)" → sp.log(self.n)
        - "n * log(n)" → self.n * sp.log(self.n)
        - "n^2" → self.n**2
        - "2^n" → 2**self.n
        """
        complexity_str = complexity_str.strip().lower()
        
        try:
            # Caso 1: Solo "1" (constante)
            if complexity_str == "1":
                return 1
            
            # Caso 2: Solo "n"
            if complexity_str == "n":
                return self.n
            
            # Caso 3: Logaritmo solo → log(n)
            if complexity_str in ("log(n)", "log n", "logn"):
                return sp.log(self.n)
            
            # Caso 4: n * log(n)
            if "log" in complexity_str and "*" in complexity_str:
                # "n * log(n)" o "n*log(n)"
                if complexity_str.startswith("n"):
                    # Extraer exponente si existe: "n^2 * log(n)"
                    if "^" in complexity_str.split("*")[0]:
                        exp = int(complexity_str.split("^")[1].split("*")[0].strip())
                        return (self.n ** exp) * sp.log(self.n)
                    else:
                        return self.n * sp.log(self.n)
            
            # Caso 5: Potencias → n^2, n^3
            if "^" in complexity_str and "log" not in complexity_str:
                if complexity_str.startswith("n^"):
                    exp_str = complexity_str.replace("n^", "").strip()
                    try:
                        exp = float(exp_str)
                        return self.n ** exp
                    except:
                        pass
            
            # Caso 6: Exponenciales → 2^n
            if "^n" in complexity_str:
                base = complexity_str.split("^")[0].strip()
                try:
                    base_num = int(base)
                    return base_num ** self.n
                except:
                    return 2 ** self.n
            
            # Caso 7: Exponencial con multiplicación → n * 2^n
            if "*" in complexity_str and "^n" in complexity_str:
                parts = complexity_str.split("*")
                if "n" in parts[0] and "^n" in parts[1]:
                    # Extraer base: "2^n" → 2
                    base = parts[1].strip().split("^")[0].strip()
                    base_num = int(base) if base.isdigit() else 2
                    
                    # Verificar si hay exponente en n: "n^2 * 2^n"
                    if "^" in parts[0]:
                        n_exp = int(parts[0].split("^")[1].strip())
                        return (self.n ** n_exp) * (base_num ** self.n)
                    else:
                        return self.n * (base_num ** self.n)
            
            # Caso 8: Intentar parsear con sympy (fallback)
            # Reemplazar ^ por **
            complexity_str_py = complexity_str.replace("^", "**")
            # Reemplazar log(n) por log(n, base)
            complexity_str_py = complexity_str_py.replace("log(n)", "log(n)")
            
            # Crear espacio de nombres para eval seguro
            namespace = {
                'n': self.n,
                'log': sp.log,
                'sqrt': sp.sqrt,
                'sp': sp
            }
            
            result = eval(complexity_str_py, {"__builtins__": {}}, namespace)
            return result
        
        except Exception as e:
            # Si todo falla, asumir lineal
            self.steps.append(
                f"    ⚠️ No se pudo parsear '{complexity_str}': {e}\n"
                f"    Asumiendo O(n) por seguridad"
            )
            return self.n
    
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
            
            # AÑADIR: Eliminar coeficientes constantes
            # 2*n → n, 3*n² → n²
            if isinstance(simplified, sp.Mul):
                # Obtener solo los términos no constantes
                args = simplified.args
                non_const_args = [arg for arg in args if not arg.is_number]
                
                if non_const_args:
                    if len(non_const_args) == 1:
                        return non_const_args[0]
                    else:
                        return sp.Mul(*non_const_args)
            
            # Extraer término dominante de sumas
            if isinstance(simplified, sp.Add):
                terms = simplified.as_ordered_terms()
                dominant = terms[-1]
                # Aplicar recursivamente para eliminar constantes
                return self._simplify_complexity(dominant)
            
            return simplified
        except:
            return expr
    
    def _generate_explanation(self, complexity) -> str:
        """Genera explicación textual del análisis"""
        explanation = "ANÁLISIS DE COMPLEJIDAD:\n\n"
        
        for step in self.steps:
            explanation += step + "\n"
        
        # Calcular versiones simplificadas
        worst_simplified = self._simplify_complexity(complexity['worst'])
        best_simplified = self._simplify_complexity(complexity['best'])
        average_simplified = self._simplify_complexity(complexity['average'])
        
        # AÑADIR: Versiones sin simplificar para caso promedio
        average_detailed = sp.simplify(complexity['average'])
        
        explanation += f"\n=== RESULTADO FINAL ===\n"
        explanation += f"Peor caso (Big-O):     O({worst_simplified})\n"
        explanation += f"Mejor caso (Omega):    Ω({best_simplified})\n"
        
        # Mostrar versión detallada si es diferente
        if str(average_detailed) != str(average_simplified):
            explanation += f"Caso promedio (Theta): Θ({average_detailed}) ≈ Θ({average_simplified})\n"
        else:
            explanation += f"Caso promedio (Theta): Θ({average_simplified})\n"
        
        # ← NUEVO: Agregar resumen de recurrencias resueltas
        if self.recurrence_solutions:
            explanation += f"\n=== RELACIONES DE RECURRENCIA RESUELTAS ===\n"
            for proc_name, sol in self.recurrence_solutions.items():
                explanation += f"\n{proc_name}:\n"
                explanation += f"  {sol['relation']}\n"
                explanation += f"  Solución: {sol['solution']}\n"
                explanation += f"  Método: {sol['method']}\n"
        
        return explanation