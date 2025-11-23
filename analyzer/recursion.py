"""
Módulo para detectar y analizar recursión en procedimientos
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass


@dataclass
class RecursionInfo:
    """Información sobre la recursión de un procedimiento"""
    is_recursive: bool
    recursion_type: str  # 'direct', 'indirect', 'tail', 'none'
    call_count: int      # Número de llamadas recursivas en el cuerpo
    calls_to: List[str]  # Lista de procedimientos que llama
    depth_pattern: str   # 'linear', 'tree', 'unknown'
    
    def __str__(self):
        if not self.is_recursive:
            return "No recursivo"
        return f"Recursivo ({self.recursion_type}), {self.call_count} llamada(s)"


class RecursionDetector:
    """
    Detecta y analiza patrones de recursión en el AST
    """
    
    def __init__(self, ast):
        self.ast = ast
        self.procedures = {}  # {nombre: ast_del_procedimiento}
        self.recursion_info = {}  # {nombre: RecursionInfo}
        self.call_graph = {}  # {procedimiento: [llamadas_que_hace]}
        
    def analyze(self) -> Dict[str, RecursionInfo]:
        """
        Analiza todos los procedimientos y detecta recursión
        
        Returns:
            Dict con información de recursión para cada procedimiento
        """
        # 1. Registrar todos los procedimientos
        self._register_procedures()
        
        # 2. Construir grafo de llamadas
        self._build_call_graph()
        
        # 3. Detectar recursión directa
        self._detect_direct_recursion()
        
        # 4. Detectar recursión indirecta
        self._detect_indirect_recursion()
        
        # 5. Detectar tail recursion
        self._detect_tail_recursion()
        
        # 6. Analizar patrón de profundidad
        self._analyze_depth_pattern()
        
        return self.recursion_info
    
    def _register_procedures(self):
        """Registra todos los procedimientos del AST"""
        if "procedures" not in self.ast:
            return
        
        for proc in self.ast["procedures"]:
            name = proc["name"]
            self.procedures[name] = proc
            self.recursion_info[name] = RecursionInfo(
                is_recursive=False,
                recursion_type='none',
                call_count=0,
                calls_to=[],
                depth_pattern='unknown'
            )
    
    def _build_call_graph(self):
        """Construye el grafo de llamadas entre procedimientos"""
        for proc_name, proc_ast in self.procedures.items():
            calls = self._find_all_calls(proc_ast["body"])
            self.call_graph[proc_name] = calls
            self.recursion_info[proc_name].calls_to = calls
    
    def _find_all_calls(self, node) -> List[str]:
        """
        Encuentra todas las llamadas a procedimientos en un nodo
        
        Returns:
            Lista de nombres de procedimientos llamados
        """
        calls = []
        
        if isinstance(node, dict):
            if node.get("type") == "call":
                calls.append(node["name"])
            
            # Recorrer recursivamente todos los valores
            for value in node.values():
                calls.extend(self._find_all_calls(value))
        
        elif isinstance(node, list):
            for item in node:
                calls.extend(self._find_all_calls(item))
        
        return calls
    
    def _detect_direct_recursion(self):
        """
        Detecta recursión directa: un procedimiento que se llama a sí mismo
        
        Ejemplo:
        procedure Factorial(n, resultado)
        begin
            if (n = 0) then
                resultado 🡨 1
            else
                CALL Factorial(n-1, resultado)  ← Recursión directa
        end
        """
        for proc_name in self.procedures.keys():
            calls = self.call_graph.get(proc_name, [])
            
            # Contar cuántas veces se llama a sí mismo
            recursive_calls = calls.count(proc_name)
            
            if recursive_calls > 0:
                self.recursion_info[proc_name].is_recursive = True
                self.recursion_info[proc_name].recursion_type = 'direct'
                self.recursion_info[proc_name].call_count = recursive_calls
    
    def _detect_indirect_recursion(self):
        """
        Detecta recursión indirecta: A llama a B, B llama a A
        
        Ejemplo:
        procedure A()
        begin
            CALL B()
        end
        
        procedure B()
        begin
            CALL A()  ← Recursión indirecta
        end
        """
        for proc_name in self.procedures.keys():
            if self.recursion_info[proc_name].is_recursive:
                continue  # Ya es recursivo directo
            
            # Verificar si hay ciclo en el grafo de llamadas
            if self._has_cycle(proc_name, set(), [proc_name]):
                self.recursion_info[proc_name].is_recursive = True
                self.recursion_info[proc_name].recursion_type = 'indirect'
    
    def _has_cycle(self, current: str, visited: Set[str], path: List[str]) -> bool:
        """
        Detecta ciclos en el grafo de llamadas usando DFS
        
        Args:
            current: Procedimiento actual
            visited: Procedimientos ya visitados
            path: Camino actual de llamadas
            
        Returns:
            True si hay un ciclo
        """
        if current in visited:
            return current in path
        
        visited.add(current)
        
        for callee in self.call_graph.get(current, []):
            if callee in self.procedures:  # Solo procedimientos definidos
                if self._has_cycle(callee, visited, path + [callee]):
                    return True
        
        return False
    
    def _detect_tail_recursion(self):
        """
        Detecta tail recursion: la llamada recursiva es la última operación
        
        Ejemplo de tail recursion:
        procedure Factorial(n, acumulador)
        begin
            if (n = 0) then
                resultado 🡨 acumulador
            else
                CALL Factorial(n-1, n*acumulador)  ← Última operación
        end
        """
        for proc_name, proc_ast in self.procedures.items():
            if not self.recursion_info[proc_name].is_recursive:
                continue
            
            if self._is_tail_recursive(proc_name, proc_ast["body"]):
                self.recursion_info[proc_name].recursion_type = 'tail'
    
    def _is_tail_recursive(self, proc_name: str, node) -> bool:
        """
        Verifica si todas las llamadas recursivas son tail calls
        
        Una tail call es cuando la llamada recursiva es la última
        operación antes del return
        """
        if isinstance(node, dict):
            node_type = node.get("type")
            
            # Si es un bloque, verificar el último statement
            if node_type == "block":
                body = node.get("body", [])
                if body:
                    return self._is_tail_recursive(proc_name, body[-1])
            
            # Si es IF, verificar ambas ramas
            elif node_type == "if":
                then_tail = self._is_tail_recursive(proc_name, node["then"])
                else_tail = self._is_tail_recursive(proc_name, node["else"])
                return then_tail and else_tail
            
            # Si es una llamada al mismo procedimiento, es tail call
            elif node_type == "call":
                return node["name"] == proc_name
            
            # Para otros tipos de nodos, buscar en sus hijos
            for value in node.values():
                if isinstance(value, (dict, list)):
                    # Si hay alguna llamada que no sea tail, retornar False
                    pass
        
        elif isinstance(node, list):
            if node:
                return self._is_tail_recursive(proc_name, node[-1])
        
        return False
    
    def _analyze_depth_pattern(self):
        """
        Analiza el patrón de profundidad de la recursión
        
        Patrones:
        - linear: T(n) = T(n-1) + O(1)  → Fibonacci, Factorial
        - tree: T(n) = 2*T(n/2) + O(1)  → Merge Sort, Quick Sort
        - unknown: No se puede determinar
        """
        for proc_name, proc_ast in self.procedures.items():
            if not self.recursion_info[proc_name].is_recursive:
                continue
            
            pattern = self._infer_depth_pattern(proc_name, proc_ast["body"])
            self.recursion_info[proc_name].depth_pattern = pattern
    
    def _infer_depth_pattern(self, proc_name: str, node) -> str:
        """
        Infiere el patrón de recursión analizando las llamadas
        
        Returns:
            'linear', 'tree', o 'unknown'
        """
        recursive_calls = self._count_recursive_calls_in_body(proc_name, node)
        
        if recursive_calls == 1:
            return 'linear'  # Una llamada → recursión lineal
        elif recursive_calls >= 2:
            return 'tree'    # Múltiples llamadas → árbol de recursión
        else:
            return 'unknown'
    
    def _count_recursive_calls_in_body(self, proc_name: str, node) -> int:
        """Cuenta llamadas recursivas directas en el cuerpo"""
        count = 0
        
        if isinstance(node, dict):
            if node.get("type") == "call" and node.get("name") == proc_name:
                return 1
            
            for value in node.values():
                count += self._count_recursive_calls_in_body(proc_name, value)
        
        elif isinstance(node, list):
            for item in node:
                count += self._count_recursive_calls_in_body(proc_name, item)
        
        return count
    
    def print_report(self):
        """Imprime un reporte detallado del análisis de recursión"""
        print("=" * 70)
        print("ANÁLISIS DE RECURSIÓN")
        print("=" * 70)
        
        if not self.procedures:
            print("No hay procedimientos definidos.")
            return
        
        for proc_name, info in self.recursion_info.items():
            print(f"\n📌 Procedimiento: {proc_name}")
            print(f"   Recursivo: {'✅ SÍ' if info.is_recursive else '❌ NO'}")
            
            if info.is_recursive:
                print(f"   Tipo: {info.recursion_type}")
                print(f"   Llamadas recursivas: {info.call_count}")
                print(f"   Patrón de profundidad: {info.depth_pattern}")
            
            if info.calls_to:
                print(f"   Llama a: {', '.join(info.calls_to)}")
        
        print("\n" + "=" * 70)


# ========================================
# EJEMPLOS DE USO Y TESTS
# ========================================

def test_direct_recursion():
    """Test: Recursión directa - Factorial"""
    ast = {
        "type": "program",
        "classes": [],
        "procedures": [
            {
                "type": "procedure_decl",
                "name": "Factorial",
                "params": [
                    {"type": "primitive_param", "name": "n"},
                    {"type": "primitive_param", "name": "resultado"}
                ],
                "body": {
                    "type": "block",
                    "body": [
                        {
                            "type": "if",
                            "cond": {"type": "binop", "op": "EQ", 
                                   "left": {"type": "var", "value": "n"},
                                   "right": {"type": "number", "value": 0}},
                            "then": {
                                "type": "block",
                                "body": [
                                    {"type": "assign", 
                                     "target": {"type": "var", "value": "resultado"},
                                     "expr": {"type": "number", "value": 1}}
                                ]
                            },
                            "else": {
                                "type": "block",
                                "body": [
                                    {"type": "call", 
                                     "name": "Factorial",
                                     "args": [
                                         {"type": "binop", "op": "MINUS",
                                          "left": {"type": "var", "value": "n"},
                                          "right": {"type": "number", "value": 1}},
                                         {"type": "var", "value": "temp"}
                                     ]}
                                ]
                            }
                        }
                    ]
                }
            }
        ],
        "body": []
    }
    
    detector = RecursionDetector(ast)
    result = detector.analyze()
    
    print("\n" + "=" * 70)
    print("TEST 1: FACTORIAL (Recursión directa)")
    print("=" * 70)
    detector.print_report()
    
    # Verificaciones
    assert result["Factorial"].is_recursive == True
    assert result["Factorial"].recursion_type == "direct"
    assert result["Factorial"].depth_pattern == "linear"
    print("\n✅ Test pasado!")


def test_indirect_recursion():
    """Test: Recursión indirecta"""
    ast = {
        "type": "program",
        "classes": [],
        "procedures": [
            {
                "type": "procedure_decl",
                "name": "A",
                "params": [],
                "body": {
                    "type": "block",
                    "body": [
                        {"type": "call", "name": "B", "args": []}
                    ]
                }
            },
            {
                "type": "procedure_decl",
                "name": "B",
                "params": [],
                "body": {
                    "type": "block",
                    "body": [
                        {"type": "call", "name": "A", "args": []}
                    ]
                }
            }
        ],
        "body": []
    }
    
    detector = RecursionDetector(ast)
    result = detector.analyze()
    
    print("\n" + "=" * 70)
    print("TEST 2: RECURSIÓN INDIRECTA (A ↔ B)")
    print("=" * 70)
    detector.print_report()
    
    # Verificaciones
    assert result["A"].is_recursive == True
    assert result["B"].is_recursive == True
    assert result["A"].recursion_type == "indirect"
    print("\n✅ Test pasado!")


def test_tree_recursion():
    """Test: Recursión tipo árbol - Fibonacci"""
    ast = {
        "type": "program",
        "classes": [],
        "procedures": [
            {
                "type": "procedure_decl",
                "name": "Fibonacci",
                "params": [{"type": "primitive_param", "name": "n"}],
                "body": {
                    "type": "block",
                    "body": [
                        {
                            "type": "if",
                            "cond": {"type": "binop", "op": "LE",
                                   "left": {"type": "var", "value": "n"},
                                   "right": {"type": "number", "value": 1}},
                            "then": {
                                "type": "block",
                                "body": [
                                    {"type": "assign",
                                     "target": {"type": "var", "value": "resultado"},
                                     "expr": {"type": "var", "value": "n"}}
                                ]
                            },
                            "else": {
                                "type": "block",
                                "body": [
                                    {"type": "call", "name": "Fibonacci",
                                     "args": [{"type": "binop", "op": "MINUS",
                                             "left": {"type": "var", "value": "n"},
                                             "right": {"type": "number", "value": 1}}]},
                                    {"type": "call", "name": "Fibonacci",
                                     "args": [{"type": "binop", "op": "MINUS",
                                             "left": {"type": "var", "value": "n"},
                                             "right": {"type": "number", "value": 2}}]}
                                ]
                            }
                        }
                    ]
                }
            }
        ],
        "body": []
    }
    
    detector = RecursionDetector(ast)
    result = detector.analyze()
    
    print("\n" + "=" * 70)
    print("TEST 3: FIBONACCI (Recursión tipo árbol)")
    print("=" * 70)
    detector.print_report()
    
    # Verificaciones
    assert result["Fibonacci"].is_recursive == True
    assert result["Fibonacci"].recursion_type == "direct"
    assert result["Fibonacci"].depth_pattern == "tree"
    print("\n✅ Test pasado!")


if __name__ == "__main__":
    test_direct_recursion()
    test_indirect_recursion()
    test_tree_recursion()
    
    print("\n" + "=" * 70)
    print("🎉 TODOS LOS TESTS PASARON")
    print("=" * 70)