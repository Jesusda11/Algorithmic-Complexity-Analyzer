"""
Enhanced Recursion Detector
- Detects direct, indirect, tail recursion
- Infers depth pattern: linear, tree, divide_and_conquer, unknown
- Infers subproblem size when possible (n-1, n/2, n/k, slice)
- Detects presence of combining (merge) work (linear combine)
- Heuristics to identify MergeSort-like and QuickSort-like patterns

Compatible with the AST shape shown in the conversation (nodes with
"type": "call"/"assign"/"while"/"for"/etc., and binop operators like
"PLUS", "MINUS", "DIV_INT", "AND", "LE", etc.).

Usage:
    detector = RecursionDetector(ast)
    info = detector.analyze()
    detector.print_report()

"""
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class RecursionInfo:
    is_recursive: bool
    recursion_type: str  # 'direct', 'indirect', 'tail', 'none'
    call_count: int      # Número de llamadas recursivas en el cuerpo
    calls_to: List[str]  # Lista de procedimientos que llama
    depth_pattern: str   # 'linear', 'tree', 'divide_and_conquer', 'unknown'
    subproblem: str = 'unknown'  # 'n-1', 'n/2', 'n/k', 'slice', 'unknown'
    has_combining_work: bool = False  # e.g. merge phase linear work

    def __str__(self):
        if not self.is_recursive:
            return "No recursivo"
        return (
            f"Recursivo ({self.recursion_type}), {self.call_count} llamada(s), "
            f"patrón={self.depth_pattern}, subproblem={self.subproblem}, combine={self.has_combining_work}"
        )


class RecursionDetector:
    """Detecta y analiza patrones de recursión en el AST con heurísticas
    para divide-and-conquer (MergeSort/QuickSort).
    """

    def __init__(self, ast: Dict):
        self.ast = ast
        self.procedures: Dict[str, Dict] = {}
        self.recursion_info: Dict[str, RecursionInfo] = {}
        self.call_graph: Dict[str, List[str]] = {}

    def analyze(self) -> Dict[str, RecursionInfo]:
        self._register_procedures()
        self._build_call_graph()
        self._detect_direct_recursion()
        self._detect_indirect_recursion()
        self._detect_tail_recursion()
        self._analyze_depth_pattern()
        return self.recursion_info

    def _register_procedures(self):
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
        for proc_name, proc_ast in self.procedures.items():
            calls = self._find_all_calls(proc_ast.get("body"))
            self.call_graph[proc_name] = calls
            self.recursion_info[proc_name].calls_to = calls

    def _find_all_calls(self, node) -> List[str]:
        calls: List[str] = []
        if isinstance(node, dict):
            if node.get("type") in ("call", "call_expr"):
                calls.append(node.get("name"))
            for value in node.values():
                if isinstance(value, (dict, list)):
                    calls.extend(self._find_all_calls(value))
        elif isinstance(node, list):
            for item in node:
                calls.extend(self._find_all_calls(item))
        return calls

    def _detect_direct_recursion(self):
        for proc_name in self.procedures.keys():
            calls = self.call_graph.get(proc_name, [])
            recursive_calls = calls.count(proc_name)
            if recursive_calls > 0:
                self.recursion_info[proc_name].is_recursive = True
                self.recursion_info[proc_name].recursion_type = 'direct'
                self.recursion_info[proc_name].call_count = recursive_calls

    def _detect_indirect_recursion(self):
        for proc_name in self.procedures.keys():
            if self.recursion_info[proc_name].is_recursive:
                continue
            if self._has_cycle(proc_name, set(), [proc_name]):
                self.recursion_info[proc_name].is_recursive = True
                self.recursion_info[proc_name].recursion_type = 'indirect'

    def _has_cycle(self, current: str, visited: Set[str], path: List[str]) -> bool:
        if current in visited:
            return current in path
        visited.add(current)
        for callee in self.call_graph.get(current, []):
            if callee in self.procedures:
                if self._has_cycle(callee, visited, path + [callee]):
                    return True
        return False

    def _detect_tail_recursion(self):
        for proc_name, proc_ast in self.procedures.items():
            if not self.recursion_info[proc_name].is_recursive:
                continue
            if self._is_tail_recursive(proc_name, proc_ast.get("body")):
                self.recursion_info[proc_name].recursion_type = 'tail'

    def _is_tail_recursive(self, proc_name: str, node) -> bool:
        if isinstance(node, dict):
            t = node.get("type")
            if t == "block":
                body = node.get("body", [])
                if body:
                    return self._is_tail_recursive(proc_name, body[-1])
            elif t == "if":
                then_tail = self._is_tail_recursive(proc_name, node.get("then"))
                else_tail = self._is_tail_recursive(proc_name, node.get("else"))
                return then_tail and else_tail
            # ✅ Aceptar tanto "call" como "call_expr"
            elif t in ("call", "call_expr"):
                return node.get("name") == proc_name
            else:
                # traverse children
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        if not self._is_tail_recursive(proc_name, v):
                            return False
                return True
        elif isinstance(node, list):
            if node:
                return self._is_tail_recursive(proc_name, node[-1])
        return False

    # -------------------------
    # Depth & Subproblem analysis
    # -------------------------
    def _analyze_depth_pattern(self):
        for proc_name, proc_ast in self.procedures.items():
            if not self.recursion_info[proc_name].is_recursive:
                continue
            body = proc_ast.get("body")
            count = self._count_recursive_calls_in_body(proc_name, body)
            # Infer subproblem information
            subproblem = self._infer_subproblem_from_proc(proc_name, body)
            has_combine = self._has_combining_work(body)

            self.recursion_info[proc_name].subproblem = subproblem
            self.recursion_info[proc_name].has_combining_work = has_combine

            if count == 1:
                # linear-like, but could be divide-and-conquer with one recursive call
                if subproblem.startswith('n/'):
                    self.recursion_info[proc_name].depth_pattern = 'divide_and_conquer'
                else:
                    self.recursion_info[proc_name].depth_pattern = 'linear'
            elif count >= 2:
                # multiple calls: could be tree or divide-and-conquer
                if subproblem.startswith('n/'):
                    self.recursion_info[proc_name].depth_pattern = 'divide_and_conquer'
                else:
                    self.recursion_info[proc_name].depth_pattern = 'tree'
            else:
                self.recursion_info[proc_name].depth_pattern = 'unknown'

    def _count_recursive_calls_in_body(self, proc_name: str, node) -> int:
        count = 0
        if isinstance(node, dict):
            if node.get("type") in ("call", "call_expr") and node.get("name") == proc_name:
                count += 1
            for v in node.values():
                if isinstance(v, (dict, list)):
                    count += self._count_recursive_calls_in_body(proc_name, v)
        elif isinstance(node, list):
            for item in node:
                count += self._count_recursive_calls_in_body(proc_name, item)
        return count

    def _infer_subproblem_from_proc(self, proc_name: str, body) -> str:
        """Heurísticas para inferir el tamaño del subproblema usado en llamadas recursivas.
        Trata de detectar patrones comunes:
          - uso de una variable "medio" calculada como (inicio + fin) / 2
          - paso de argumentos "medio - 1" o "medio + 1"
          - división directa n/2
          - restas por 1 (n-1)
          - slices/subarray usage
        """
        # 1) Detectar asignación de punto medio (medio = (inicio + fin) DIV 2)
        midpoint_vars = self._find_midpoint_variables(body)

        # 2) Buscar llamadas recursivas y analizar sus argumentos
        calls = self._find_recursive_call_nodes(proc_name, body)
        if not calls:
            return 'unknown'

        # Collect evidence
        evidence = []
        for call in calls:
            args = call.get('args', [])
            if not args:
                continue
            # Usually the problem size is represented via the third/fourth args (inicio/fin) in divide & conquer
            for arg in args:
                # Case: binop DIV_INT or DIV with right == 2
                if isinstance(arg, dict) and arg.get('type') == 'binop' and arg.get('op') in ('DIV', 'DIV_INT'):
                    right = arg.get('right', {})
                    if right.get('type') == 'number' and right.get('value') == 2:
                        evidence.append('n/2')
                # Case: argument uses midpoint variable or medio-1 / medio+1
                if isinstance(arg, dict) and arg.get('type') == 'binop' and arg.get('op') in ('MINUS', 'PLUS'):
                    left = arg.get('left', {})
                    right = arg.get('right', {})
                    # medio - 1 or medio + 1
                    if left.get('type') == 'var' and left.get('value') in midpoint_vars:
                        if right.get('type') == 'number' and right.get('value') == 1:
                            evidence.append('n/2')
                if isinstance(arg, dict) and arg.get('type') == 'var' and arg.get('value') in midpoint_vars:
                    evidence.append('n/2')
                # Case: subtraction by 1 of the main parameter (n-1)
                if isinstance(arg, dict) and arg.get('type') == 'binop' and arg.get('op') == 'MINUS':
                    right = arg.get('right', {})
                    if right.get('type') == 'number' and right.get('value') == 1:
                        evidence.append('n-1')
                # Case: slice/subarray (heuristic)
                if isinstance(arg, dict) and arg.get('type') in ('slice', 'subarray'):
                    evidence.append('slice')

        # Decide
        if 'n/2' in evidence:
            return 'n/2'
        if 'slice' in evidence:
            return 'slice'
        if 'n-1' in evidence and 'n/2' not in evidence:
            return 'n-1'
        return 'unknown'

    def _find_midpoint_variables(self, node) -> Set[str]:
        """Busca variables asignadas como (inicio + fin) / 2 y devuelve sus nombres.
        Heurística: busca asignaciones donde expr es binop DIV_INT with left binop PLUS of inicio and fin.
        """
        found = set()
        if isinstance(node, dict):
            if node.get('type') == 'assign':
                target = node.get('target', {})
                expr = node.get('expr', {})
                if target.get('type') == 'var' and isinstance(expr, dict):
                    if expr.get('type') == 'binop' and expr.get('op') in ('DIV_INT', 'DIV'):
                        left = expr.get('left', {})
                        right = expr.get('right', {})
                        if isinstance(left, dict) and left.get('type') == 'binop' and left.get('op') in ('PLUS',):
                            # we assume variables are named inicio and fin or similar
                            l = left.get('left', {})
                            r = left.get('right', {})
                            if l.get('type') == 'var' and r.get('type') == 'var':
                                # nothing strict, add the var name
                                found.add(target.get('value'))
            for v in node.values():
                if isinstance(v, (dict, list)):
                    found |= self._find_midpoint_variables(v)
        elif isinstance(node, list):
            for item in node:
                found |= self._find_midpoint_variables(item)
        return found

    def _find_recursive_call_nodes(self, proc_name: str, node) -> List[Dict]:
        nodes: List[Dict] = []
        if isinstance(node, dict):
            if node.get('type') in ('call', 'call_expr') and node.get('name') == proc_name:
                nodes.append(node)
            for v in node.values():
                if isinstance(v, (dict, list)):
                    nodes.extend(self._find_recursive_call_nodes(proc_name, v))
        elif isinstance(node, list):
            for item in node:
                nodes.extend(self._find_recursive_call_nodes(proc_name, item))
        return nodes

    def _has_combining_work(self, node) -> bool:
        """Detecta si el procedimiento tiene trabajo de combinación lineal típico
        (por ejemplo bucles que copian entre Temp y A). Heurística:
          - busca while con op 'AND' y array_access en condiciones o bodies
          - o múltiples while/for que incrementan índices y usan Temp
        """
        combines = 0
        if isinstance(node, dict):
            t = node.get('type')
            if t == 'while':
                cond = node.get('cond', {})
                # AND condition in merge main loop
                if isinstance(cond, dict) and cond.get('type') == 'binop' and cond.get('op') == 'AND':
                    combines += 1
                # examine body for array copies
                body = node.get('body')
                if body and self._body_contains_array_copy(body):
                    combines += 1
            for v in node.values():
                if isinstance(v, (dict, list)):
                    if self._has_combining_work(v):
                        combines += 1
        elif isinstance(node, list):
            for item in node:
                if self._has_combining_work(item):
                    combines += 1
        return combines > 0

    def _body_contains_array_copy(self, body) -> bool:
        # Heuristic: look for assignments where target is array_access and expr is array_access
        if isinstance(body, dict) and body.get('type') == 'block':
            for stmt in body.get('body', []):
                if stmt.get('type') == 'assign':
                    target = stmt.get('target', {})
                    expr = stmt.get('expr', {})
                    if target.get('type') == 'array_access' and expr.get('type') == 'array_access':
                        return True
                # deeper
                if self._body_contains_array_copy(stmt):
                    return True
        elif isinstance(body, list):
            for stmt in body:
                if self._body_contains_array_copy(stmt):
                    return True
        elif isinstance(body, dict):
            for v in body.values():
                if isinstance(v, (dict, list)) and self._body_contains_array_copy(v):
                    return True
        return False

    # -------------------------
    # Utilities & reporting
    # -------------------------
    def print_report(self):
        print("=" * 70)
        print("ANÁLISIS DE RECURSIÓN (MEJORADO)")
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
                print(f"   Subproblema: {info.subproblem}")
                print(f"   Trabajo de combinación detectado: {'✅ SÍ' if info.has_combining_work else '❌ NO'}")
            if info.calls_to:
                print(f"   Llama a: {', '.join(info.calls_to)}")
        print("\n" + "=" * 70)


# ========================================
# TESTS (incluye MergeSort)
# ========================================

def test_mergesort_detection():
    # AST mínimo para MergeSort (similar al ejemplo previo)
    ast = {
        "type": "program",
        "procedures": [
            {
                "type": "procedure_decl",
                "name": "MergeSort",
                "params": [],
                "body": {
                    "type": "block",
                    "body": [
                        {   # medio = (inicio + fin) div 2
                            "type": "assign",
                            "target": {"type": "var", "value": "medio"},
                            "expr": {
                                "type": "binop",
                                "op": "DIV_INT",
                                "left": {"type": "binop", "op": "PLUS", "left": {"type": "var", "value": "inicio"}, "right": {"type": "var", "value": "fin"}},
                                "right": {"type": "number", "value": 2}
                            }
                        },
                        {   # call MergeSort(..., inicio, medio)
                            "type": "call",
                            "name": "MergeSort",
                            "args": [ {"type": "var", "value": "A"}, {"type": "var", "value": "inicio"}, {"type": "var", "value": "medio"} ]
                        },
                        {   # call MergeSort(..., medio+1, fin)
                            "type": "call",
                            "name": "MergeSort",
                            "args": [ {"type": "var", "value": "A"}, {"type": "binop", "op": "PLUS", "left": {"type": "var", "value": "medio"}, "right": {"type": "number", "value": 1}}, {"type": "var", "value": "fin"} ]
                        },
                        {   # merge work: while cond with AND and array copies
                            "type": "while",
                            "cond": {"type": "binop", "op": "AND"},
                            "body": {"type": "block", "body": [
                                {"type": "assign", "target": {"type": "array_access"}, "expr": {"type": "array_access"}},
                                {"type": "assign", "target": {"type": "var", "value": "i"}, "expr": {"type": "binop", "op": "PLUS"}}
                            ]}
                        }
                    ]
                }
            }
        ]
    }

    detector = RecursionDetector(ast)
    info = detector.analyze()
    detector.print_report()

    ms_info = info.get('MergeSort')
    assert ms_info is not None
    assert ms_info.is_recursive
    assert ms_info.depth_pattern == 'divide_and_conquer'
    assert ms_info.subproblem == 'n/2'
    assert ms_info.has_combining_work == True
    print('\n✅ Test MERGESORT detectado correctamente')


if __name__ == '__main__':
    test_mergesort_detection()
