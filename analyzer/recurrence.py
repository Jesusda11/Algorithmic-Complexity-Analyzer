"""
Solver de Relaciones de Recurrencia (MEJORADO)
Detecta correctamente divide-and-conquer con condicionales
"""

import sympy as sp
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class RecurrenceRelation:
    """Representa una relación de recurrencia"""
    a: int  # Número de llamadas recursivas ACTIVAS
    b: int  # Factor de división del problema
    f_complexity: str  # Complejidad de f(n): "1", "n", "n^2", "n*log(n)"
    reduction_type: str  # "divide" (n/2), "subtract" (n-1)
    
    def __str__(self):
        if self.reduction_type == "divide":
            return f"T(n) = {self.a}T(n/{self.b}) + O({self.f_complexity})"
        else:
            return f"T(n) = {self.a}T(n-{self.b}) + O({self.f_complexity})"


@dataclass
class RecurrenceSolution:
    """Solución de una relación de recurrencia"""
    relation: str
    complexity: str
    method: str
    explanation: str
    
    def __str__(self):
        return f"{self.relation} → {self.complexity}"


class RecurrenceSolver:
    """
    Resuelve relaciones de recurrencia usando:
    1. Master Theorem (para divide y conquista)
    2. Análisis directo (para recursión lineal)
    3. Expansion method (casos generales)
    """
    
    def __init__(self):
        self.n = sp.Symbol('n', positive=True, integer=True)
        self.procedures = {} 
    
    def solve(self, recurrence: RecurrenceRelation) -> RecurrenceSolution:
        """Punto de entrada para resolver una relación de recurrencia"""
        if recurrence.reduction_type == "divide":
            return self._solve_divide_and_conquer(recurrence)
        elif recurrence.reduction_type == "subtract":
            return self._solve_linear_recursion(recurrence)
        else:
            return RecurrenceSolution(
                relation=str(recurrence),
                complexity="O(?)",
                method="Unknown",
                explanation="Tipo de recursión no reconocido"
            )
    
    def _solve_divide_and_conquer(self, rec: RecurrenceRelation) -> RecurrenceSolution:
        """Resuelve T(n) = aT(n/b) + f(n) usando Master Theorem"""
        a = rec.a
        b = rec.b
        f = rec.f_complexity
        
        # Calcular c = log_b(a)
        c = math.log(a) / math.log(b)
        
        relation_str = f"T(n) = {a}T(n/{b}) + O({f})"
        
        # Analizar f(n)
        f_degree = self._get_polynomial_degree(f)
        
        # Aplicar Master Theorem
        if f_degree is not None:
            if f_degree < c:
                # Caso 1: f(n) es polinómicamente menor que n^c
                if abs(c - int(c)) < 0.01:
                    if int(c) == 0:
                        complexity = "1"
                    elif int(c) == 1:
                        complexity = "n"
                    else:
                        complexity = f"n^{int(c)}"
                else:
                    complexity = f"n^{c:.2f}"
                
                explanation = (
                    f"Master Theorem - Caso 1:\n"
                    f"  a = {a}, b = {b}, c = log_{b}({a}) = {c:.2f}\n"
                    f"  f(n) = O(n^{f_degree}) < O(n^{c:.2f})\n"
                    f"  Por tanto: T(n) = Θ({complexity})"
                )
                return RecurrenceSolution(
                    relation=relation_str,
                    complexity=f"O({complexity})",
                    method="Master Theorem - Caso 1",
                    explanation=explanation
                )
            
            elif abs(f_degree - c) < 0.01:  # f_degree ≈ c
                # Caso 2: f(n) = Θ(n^c)
                if abs(c) < 0.01:
                    complexity = "log(n)"
                elif abs(c - 1) < 0.01:
                    complexity = "n * log(n)"
                elif abs(c - int(c)) < 0.01:
                    if int(c) == 0:
                        complexity = "log(n)"
                    elif int(c) == 1:
                        complexity = "n * log(n)"
                    else:
                        complexity = f"n^{int(c)} * log(n)"
                else:
                    complexity = f"n^{c:.2f} * log(n)"
                
                explanation = (
                    f"Master Theorem - Caso 2:\n"
                    f"  a = {a}, b = {b}, c = log_{b}({a}) = {c:.2f}\n"
                    f"  f(n) = Θ(n^{f_degree}) = Θ(n^{c:.2f})\n"
                    f"  Por tanto: T(n) = Θ({complexity})"
                )
                return RecurrenceSolution(
                    relation=relation_str,
                    complexity=f"O({complexity})",
                    method="Master Theorem - Caso 2",
                    explanation=explanation
                )
            
            else:  # f_degree > c
                # Caso 3: f(n) domina
                if abs(f_degree) < 0.01:
                    complexity = "1"
                elif abs(f_degree - 1) < 0.01:
                    complexity = "n"
                elif abs(f_degree - int(f_degree)) < 0.01:
                    complexity = f"n^{int(f_degree)}"
                else:
                    complexity = f"n^{f_degree}"
                
                explanation = (
                    f"Master Theorem - Caso 3:\n"
                    f"  a = {a}, b = {b}, c = log_{b}({a}) = {c:.2f}\n"
                    f"  f(n) = Ω(n^{f_degree}) > Ω(n^{c:.2f})\n"
                    f"  f(n) domina, por tanto: T(n) = Θ({complexity})"
                )
                return RecurrenceSolution(
                    relation=relation_str,
                    complexity=f"O({complexity})",
                    method="Master Theorem - Caso 3",
                    explanation=explanation
                )
        
        # Caso especial con logaritmos
        if "log" in f:
            if a == b:
                complexity = "n * log^2(n)"
                explanation = (
                    f"Caso especial: a = b = {a}\n"
                    f"  T(n) = {a}T(n/{a}) + O(n*log n)\n"
                    f"  Por tanto: T(n) = O(n * log^2 n)"
                )
            else:
                complexity = "n * log(n)"
                explanation = f"T(n) ≈ O(n * log n) (estimación)"
            
            return RecurrenceSolution(
                relation=relation_str,
                complexity=f"O({complexity})",
                method="Master Theorem - Caso especial",
                explanation=explanation
            )
        
        # Caso por defecto
        return RecurrenceSolution(
            relation=relation_str,
            complexity="O(n * log n)",
            method="Master Theorem (estimado)",
            explanation="Relación compleja, estimación conservadora"
        )
    
    def _solve_linear_recursion(self, rec: RecurrenceRelation) -> RecurrenceSolution:
        """Resuelve T(n) = aT(n-b) + f(n)"""
        a = rec.a
        b = rec.b
        f = rec.f_complexity
        
        relation_str = f"T(n) = {a}T(n-{b}) + O({f})"
        
        f_degree = self._get_polynomial_degree(f)
        
        if a == 1:
            # T(n) = T(n-1) + f(n)
            if f_degree == 0:
                complexity = "n"
                explanation = (
                    f"Recursión lineal simple:\n"
                    f"  T(n) = T(n-1) + O(1)\n"
                    f"  Se expande a: 1 + 1 + 1 + ... (n veces)\n"
                    f"  Por tanto: T(n) = O(n)"
                )
            elif f_degree == 1:
                complexity = "n^2"
                explanation = (
                    f"Recursión con costo lineal:\n"
                    f"  T(n) = T(n-1) + O(n)\n"
                    f"  Se expande a: n + (n-1) + (n-2) + ... + 1\n"
                    f"  Suma aritmética = n(n+1)/2\n"
                    f"  Por tanto: T(n) = O(n^2)"
                )
            else:
                complexity = f"n^{f_degree + 1}"
                explanation = (
                    f"Recursión con costo polinómico:\n"
                    f"  T(n) = T(n-1) + O(n^{f_degree})\n"
                    f"  Por tanto: T(n) = O(n^{f_degree + 1})"
                )
        
        elif a == 2:
            # T(n) = 2T(n-1) + f(n) → Crecimiento exponencial
            if f_degree == 0:
                complexity = "2^n"
                explanation = (
                    f"Recursión exponencial:\n"
                    f"  T(n) = 2T(n-1) + O(1)\n"
                    f"  Árbol binario de altura n\n"
                    f"  Nodos totales = 2^n\n"
                    f"  Por tanto: T(n) = O(2^n)"
                )
            else:
                if f_degree == 1:
                    complexity = "n * 2^n"
                elif abs(f_degree - int(f_degree)) < 0.01:
                    complexity = f"n^{int(f_degree)} * 2^n"
                else:
                    complexity = f"n^{f_degree} * 2^n"
                
                explanation = (
                    f"Recursión exponencial con costo adicional:\n"
                    f"  T(n) = 2T(n-1) + O(n^{f_degree})\n"
                    f"  Por tanto: T(n) = O({complexity})"
                )
        
        else:
            # T(n) = aT(n-1) + f(n) → O(a^n) o mayor
            if f_degree == 0:
                complexity = f"{a}^n"
                explanation = (
                    f"Recursión con factor {a}:\n"
                    f"  T(n) = {a}T(n-1) + O(1)\n"
                    f"  Por tanto: T(n) = O({a}^n)"
                )
            else:
                if f_degree == 1:
                    complexity = f"n * {a}^n"
                elif abs(f_degree - int(f_degree)) < 0.01:
                    complexity = f"n^{int(f_degree)} * {a}^n"
                else:
                    complexity = f"n^{f_degree} * {a}^n"
                
                explanation = (
                    f"Recursión con factor {a} y costo adicional:\n"
                    f"  T(n) = {a}T(n-1) + O(n^{f_degree})\n"
                    f"  Por tanto: T(n) = O({complexity})"
                )
        
        return RecurrenceSolution(
            relation=relation_str,
            complexity=f"O({complexity})",
            method="Expansión directa",
            explanation=explanation
        )
    
    def _get_polynomial_degree(self, f_str: str) -> Optional[float]:
        """Extrae el grado del polinomio de f(n)"""
        f_str = f_str.strip().lower()
        
        if f_str == "1":
            return 0
        elif f_str == "n":
            return 1
        elif "^" in f_str:
            try:
                exp = float(f_str.split("^")[1])
                return exp
            except:
                return None
        elif "log" in f_str:
            return None
        
        return None
    
    def infer_from_ast(self, proc_name: str, proc_ast: Dict, 
                      recursion_info, procedures: Dict = None) -> Optional[RecurrenceRelation]:
        """
        🔧 VERSIÓN ACTUALIZADA: Ahora recibe 'procedures' para analizar llamadas
        
        Args:
            proc_name: Nombre del procedimiento
            proc_ast: AST del procedimiento
            recursion_info: Info de recursión
            procedures: Diccionario con TODOS los procedimientos (NUEVO)
        """
        if proc_name not in recursion_info or not recursion_info[proc_name].is_recursive:
            return None
        
        rec_info = recursion_info[proc_name]
        
        # Guardar procedures para uso en métodos auxiliares
        self.procedures = procedures or {}
        
        # PASO 1: Contar llamadas recursivas activas
        num_active_calls = self._count_active_recursive_calls(proc_ast["body"], proc_name)
        
        # PASO 2: Analizar reducción
        all_calls = self._find_recursive_calls(proc_ast["body"])
        reduction_type, reduction_factor = self._analyze_reduction_from_calls(all_calls)
        
        # PASO 3: Analizar trabajo no recursivo (AHORA con soporte para Merge)
        work_complexity = self._analyze_non_recursive_work_v2(proc_ast["body"], proc_name)
        
        return RecurrenceRelation(
            a=num_active_calls,
            b=reduction_factor,
            f_complexity=work_complexity,
            reduction_type=reduction_type
        )
    
    def _analyze_non_recursive_work_v2(self, body: Dict, proc_name: str) -> str:
        """
        🆕 VERSIÓN MEJORADA que analiza llamadas a otros procedimientos
        """
        simple_operations = 0
        has_loop = False
        max_nested_depth = 0
        max_called_complexity = "1"  # Máxima complejidad de llamadas
        
        def analyze_node(node, depth=0, loop_depth=0):
            nonlocal simple_operations, has_loop, max_nested_depth, max_called_complexity
            
            if depth > 15:
                return
            
            if isinstance(node, dict):
                node_type = node.get("type")
                
                # Detectar ciclos
                if node_type in ("for", "while", "repeat"):
                    has_loop = True
                    current_depth = loop_depth + 1
                    max_nested_depth = max(max_nested_depth, current_depth)
                    
                    if "body" in node:
                        analyze_node(node["body"], depth + 1, current_depth)
                    return
                
                # Asignaciones simples
                elif node_type == "assign" and loop_depth == 0:
                    simple_operations += 1
                
                # ← CLAVE: Analizar llamadas a OTROS procedimientos
                elif node_type == "call":
                    call_name = node.get("name", "")
                    
                    # Ignorar llamadas recursivas
                    if call_name == proc_name:
                        return
                    
                    # Analizar complejidad del procedimiento llamado
                    proc_complexity = self._get_procedure_complexity(call_name, self.procedures)
                    
                    # Actualizar la complejidad máxima
                    if self._complexity_greater_than(proc_complexity, max_called_complexity):
                        max_called_complexity = proc_complexity
                
                # Recursión en subnodos
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        analyze_node(value, depth + 1, loop_depth)
            
            elif isinstance(node, list):
                for item in node:
                    analyze_node(item, depth, loop_depth)
        
        analyze_node(body)
        
        # DECISIÓN: Combinar ciclos y llamadas
        
        # 1. Ciclos explícitos dominan
        if max_nested_depth > 0:
            return "n" if max_nested_depth == 1 else f"n^{max_nested_depth}"
        
        # 2. Llamadas a procedimientos con complejidad > O(1)
        if max_called_complexity != "1":
            return max_called_complexity
        
        # 3. Solo operaciones simples
        return "1" if simple_operations <= 20 else "n"
    
    def _complexity_greater_than(self, comp1: str, comp2: str) -> bool:
        """
        🆕 Compara dos complejidades y retorna True si comp1 > comp2
        """
        # Orden: 1 < log(n) < sqrt(n) < n < n*log(n) < n^2 < n^3 < 2^n
        order = {
            "1": 0,
            "log(n)": 1,
            "sqrt(n)": 2,
            "n": 3,
            "n*log(n)": 4,
            "n^2": 5,
            "n^3": 6,
            "2^n": 7
        }
        
        # Normalizar
        c1 = comp1.strip().lower()
        c2 = comp2.strip().lower()
        
        # Mapear a orden conocido
        rank1 = order.get(c1, 3)  # Default: n
        rank2 = order.get(c2, 3)
        
        return rank1 > rank2
    
    def _count_active_recursive_calls(self, body: Dict, proc_name: str):
        def count_in_node(node):
            if isinstance(node, dict):
                node_type = node.get("type")
                
                # Si es IF con ELSE, solo una rama se ejecuta
                if node_type == "if":
                    then_count = count_in_node(node.get("then", {}))
                    else_block = node.get("else")
                    
                    if else_block is not None:
                        # IF-THEN-ELSE: mutuamente excluyente
                        else_count = count_in_node(else_block)
                        return max(then_count, else_count)
                    else:
                        # IF-THEN sin ELSE: solo contar THEN
                        return then_count
                
                # Si es un BLOCK, sumar todas las llamadas secuenciales
                elif node_type == "block":
                    total = 0
                    for stmt in node.get("body", []):
                        total += count_in_node(stmt)
                    return total
                
                # Si es una llamada recursiva
                elif node_type == "call" and node.get("name") == proc_name:
                    return 1
                
                # Otros nodos: explorar hijos
                else:
                    total = 0
                    for value in node.values():
                        if isinstance(value, (dict, list)):
                            total += count_in_node(value)
                    return total
            
            elif isinstance(node, list):
                total = 0
                for item in node:
                    total += count_in_node(item)
                return total
            
            return 0
        
        return count_in_node(body)
    
    def _analyze_reduction_from_calls(self, calls) -> Tuple[str, int]:
        """
        🆕 Analiza TODAS las llamadas para detectar el patrón de reducción
        """
        for call in calls:
            if not call.get("args"):
                continue
            
            # Buscar argumentos que sean expresiones matemáticas
            for arg in call["args"]:
                if isinstance(arg, dict) and arg.get("type") == "binop":
                    op = arg.get("op")
                    left = arg.get("left", {})
                    right = arg.get("right", {})
                    
                    # Detectar división: medio - 1, medio + 1, donde medio = (inicio + fin) / 2
                    if op in ("MINUS", "PLUS"):
                        # Verificar si 'left' es una variable calculada como punto medio
                        if left.get("type") == "var":
                            var_name = left.get("value")
                            # Buscar si esta variable fue calculada con DIV
                            if self._is_midpoint_variable(call, var_name):
                                return ("divide", 2)
                    
                    # Detectar división directa: n / 2
                    elif op in ("DIV", "DIV_INT"):
                        if right.get("type") == "number":
                            return ("divide", right.get("value", 2))
        
        # Por defecto, asumir resta lineal
        return ("subtract", 1)
    
    def _is_midpoint_variable(self, call_context, var_name: str) -> bool:
        """
        🆕 Verifica si una variable fue calculada como punto medio
        Busca patrones como: medio = (inicio + fin) / 2
        """
        # Esta es una heurística: si la variable se llama 'medio', 'mid', 'mitad'
        # asumimos que es un punto medio
        midpoint_names = ["medio", "mid", "mitad", "middle", "m"]
        return var_name.lower() in midpoint_names
    
    def _analyze_reduction(self, body: Dict) -> Tuple[str, int]:
        """Método original (respaldo)"""
        calls = self._find_recursive_calls(body)
        
        for call in calls:
            if not call.get("args"):
                continue
            
            first_arg = call["args"][0]
            
            if isinstance(first_arg, dict):
                if first_arg.get("type") == "binop":
                    op = first_arg.get("op")
                    
                    if op == "MINUS":
                        right = first_arg.get("right", {})
                        if right.get("type") == "number":
                            return ("subtract", right.get("value", 1))
                    
                    elif op == "DIV" or op == "DIV_INT":
                        right = first_arg.get("right", {})
                        if right.get("type") == "number":
                            return ("divide", right.get("value", 2))
        
        return ("subtract", 1)
    
    def _analyze_non_recursive_work(self, body: Dict, proc_name: str) -> str:
        """
        🔧 VERSIÓN MEJORADA: Analiza el trabajo no recursivo considerando:
        1. Ciclos explícitos (for, while, repeat)
        2. Llamadas a otros procedimientos con su complejidad real
        
        Returns:
            "1", "n", "n^2", "n*log(n)", etc.
        """
        simple_operations = 0
        has_loop = False
        max_nested_depth = 0
        called_procedures_complexity = []  # ← NUEVO
        
        def analyze_node(node, depth=0, loop_depth=0):
            nonlocal simple_operations, has_loop, max_nested_depth, called_procedures_complexity
            
            if depth > 15:
                return
            
            if isinstance(node, dict):
                node_type = node.get("type")
                
                # Detectar CICLOS
                if node_type in ("for", "while", "repeat"):
                    has_loop = True
                    current_depth = loop_depth + 1
                    max_nested_depth = max(max_nested_depth, current_depth)
                    
                    if "body" in node:
                        analyze_node(node["body"], depth + 1, current_depth)
                    
                    return
                
                # Contar asignaciones SOLO fuera de ciclos
                elif node_type == "assign" and loop_depth == 0:
                    simple_operations += 1
                
                # ← NUEVO: Analizar llamadas a OTROS procedimientos
                elif node_type == "call":
                    call_name = node.get("name", "")
                    
                    # Si es recursiva, ignorar (ya se cuenta en 'a')
                    if call_name == proc_name:
                        return
                    
                    # Si es a otro procedimiento, analizar su complejidad
                    proc_complexity = self._get_procedure_complexity(call_name)
                    
                    if proc_complexity and proc_complexity != "1":
                        called_procedures_complexity.append(proc_complexity)
                    else:
                        simple_operations += 1
                
                # Analizar subnodos
                for key, value in node.items():
                    if isinstance(value, (dict, list)):
                        analyze_node(value, depth + 1, loop_depth)
            
            elif isinstance(node, list):
                for item in node:
                    analyze_node(item, depth, loop_depth)
        
        analyze_node(body)
        
        # DECISIÓN FINAL: Combinar ciclos y llamadas a procedimientos
        
        # 1. Si hay ciclos explícitos, eso domina
        if max_nested_depth > 0:
            if max_nested_depth == 1:
                return "n"
            else:
                return f"n^{max_nested_depth}"
        
        # 2. Si hay llamadas a procedimientos con complejidad O(n) o mayor
        if called_procedures_complexity:
            # Tomar la complejidad más alta
            # Por simplicidad, si alguna es "n", retornar "n"
            for comp in called_procedures_complexity:
                if "n^2" in comp:
                    return "n^2"
                elif "n" in comp:
                    return "n"
            
            # Si hay log(n), mantenerlo
            if any("log" in comp for comp in called_procedures_complexity):
                return "n*log(n)"
        
        # 3. Sin ciclos ni llamadas complejas → O(1)
        if simple_operations <= 5:
            return "1"
        elif simple_operations <= 20:
            return "1"
        else:
            # Muchas operaciones secuenciales
            return "n"


    def _get_procedure_complexity(self, proc_name: str, procedures: Dict) -> str:
        """
        🆕 Obtiene la complejidad de un procedimiento
        
        Args:
            proc_name: Nombre del procedimiento
            procedures: Diccionario con todos los procedimientos del AST
        
        Returns:
            "1", "n", "n^2", etc.
        """
        # Si está en procedures, analizarlo
        if proc_name in procedures:
            proc_ast = procedures[proc_name]
            proc_body = proc_ast.get("body", {})
            
            # Análisis rápido: ¿tiene ciclos?
            has_loop, max_depth = self._quick_loop_check(proc_body)
            
            if has_loop:
                if max_depth == 1:
                    return "n"
                elif max_depth == 2:
                    return "n^2"
                else:
                    return f"n^{max_depth}"
            else:
                return "1"
        
        # Procedimiento desconocido → asumir O(1)
        return "1"
    
    def _quick_loop_check(self, body: Dict) -> tuple:
        """
        🆕 Verifica rápidamente si hay ciclos y su profundidad
        
        Returns:
            (has_loop: bool, max_depth: int)
        """
        max_depth = 0
        
        def check_node(node, loop_depth=0):
            nonlocal max_depth
            
            if isinstance(node, dict):
                node_type = node.get("type")
                
                if node_type in ("for", "while", "repeat"):
                    current_depth = loop_depth + 1
                    max_depth = max(max_depth, current_depth)
                    
                    if "body" in node:
                        check_node(node["body"], current_depth)
                
                else:
                    for value in node.values():
                        if isinstance(value, (dict, list)):
                            check_node(value, loop_depth)
            
            elif isinstance(node, list):
                for item in node:
                    check_node(item, loop_depth)
        
        check_node(body)
        
        return (max_depth > 0, max_depth)
    
    def _find_recursive_calls(self, node, calls=None):
        """Encuentra todas las llamadas en el AST"""
        if calls is None:
            calls = []
        
        if isinstance(node, dict):
            if node.get("type") == "call":
                calls.append(node)
            
            for value in node.values():
                self._find_recursive_calls(value, calls)
        
        elif isinstance(node, list):
            for item in node:
                self._find_recursive_calls(item, calls)
        
        return calls


# ========================================
# TESTS
# ========================================

def test_binary_search_detection():
    """Test específico para Búsqueda Binaria"""
    solver = RecurrenceSolver()
    
    print("=" * 70)
    print("TEST: DETECCIÓN DE BÚSQUEDA BINARIA")
    print("=" * 70)
    
    # Simular el AST de búsqueda binaria
    binary_search_ast = {
        "type": "procedure_decl",
        "name": "BusquedaBinaria",
        "body": {
            "type": "if",
            "then": {"type": "block", "body": []},
            "else": {
                "type": "block",
                "body": [
                    {
                        "type": "if",
                        "then": {"type": "block", "body": []},
                        "else": {
                            "type": "if",
                            "then": {
                                "type": "call",
                                "name": "BusquedaBinaria",
                                "args": [
                                    {"type": "var", "value": "A"},
                                    {"type": "var", "value": "x"},
                                    {"type": "var", "value": "inicio"},
                                    {
                                        "type": "binop",
                                        "op": "MINUS",
                                        "left": {"type": "var", "value": "medio"},
                                        "right": {"type": "number", "value": 1}
                                    }
                                ]
                            },
                            "else": {
                                "type": "call",
                                "name": "BusquedaBinaria",
                                "args": [
                                    {"type": "var", "value": "A"},
                                    {"type": "var", "value": "x"},
                                    {
                                        "type": "binop",
                                        "op": "PLUS",
                                        "left": {"type": "var", "value": "medio"},
                                        "right": {"type": "number", "value": 1}
                                    },
                                    {"type": "var", "value": "fin"}
                                ]
                            }
                        }
                    }
                ]
            }
        }
    }
    
    # Simular recursion_info
    class MockRecursionInfo:
        is_recursive = True
        recursion_type = "direct"
        depth_pattern = "tree"
        call_count = 2
    
    recursion_info = {"BusquedaBinaria": MockRecursionInfo()}
    
    # Inferir relación
    relation = solver.infer_from_ast("BusquedaBinaria", binary_search_ast, recursion_info)
    
    print(f"\n✓ Relación detectada: {relation}")
    print(f"  - Llamadas activas (a): {relation.a}")
    print(f"  - Factor de división (b): {relation.b}")
    print(f"  - Tipo de reducción: {relation.reduction_type}")
    print(f"  - Trabajo no recursivo: O({relation.f_complexity})")
    
    # Resolver
    solution = solver.solve(relation)
    
    print(f"\n✓ Solución:")
    print(f"  {solution.complexity}")
    print(f"\n{solution.explanation}")
    
    # Validación
    assert relation.a == 1, f"❌ Debe detectar 1 llamada activa, no {relation.a}"
    assert relation.b == 2, f"❌ Debe detectar división por 2, no {relation.b}"
    assert relation.reduction_type == "divide", f"❌ Debe ser 'divide', no '{relation.reduction_type}'"
    assert "log" in solution.complexity.lower(), f"❌ Debe ser O(log n), no {solution.complexity}"
    
    print("\n✅ TEST PASADO: Búsqueda Binaria correctamente detectada como O(log n)")


if __name__ == "__main__":
    test_binary_search_detection()