# interpreter/hybrid_interpreter.py
from typing import Any, Dict, List, Optional, Tuple
import sympy as sp
import math

# -----------------------
# Señales de control
# -----------------------
class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value

class BreakSignal(Exception):
    pass

class ContinueSignal(Exception):
    pass

# -----------------------
# Referencia (paso por referencia)
# -----------------------
class Ref:
    def __init__(self, env, name):
        self.env = env
        self.name = name

    def get(self):
        return self.env.get(self.name)

    def set(self, value):
        self.env.set(self.name, value)

# -----------------------
# Helper: representante simbólico/concreto
# -----------------------
class SymVal:
    def __init__(self, v):
        self.v = v

    def is_symbolic(self):
        return isinstance(self.v, (sp.Expr, sp.Symbol))

    def as_sympy(self):
        if isinstance(self.v, (sp.Expr, sp.Symbol)):
            return self.v
        if isinstance(self.v, int):
            return sp.Integer(self.v)
        if isinstance(self.v, float):
            return sp.Float(self.v)
        if self.v is True:
            return sp.Integer(1)
        if self.v is False:
            return sp.Integer(0)
        return sp.Symbol(str(self.v))

    def __add__(self, other):
        if isinstance(other, SymVal):
            a = self.v; b = other.v
        else:
            a = self.v; b = other
        if isinstance(a, (sp.Expr, sp.Symbol)) or isinstance(b, (sp.Expr, sp.Symbol)):
            return SymVal(sp.simplify(sp.sympify(a) + sp.sympify(b)))
        return SymVal(a + b)

    def __sub__(self, other):
        if isinstance(other, SymVal):
            a = self.v; b = other.v
        else:
            a = self.v; b = other
        if isinstance(a, (sp.Expr, sp.Symbol)) or isinstance(b, (sp.Expr, sp.Symbol)):
            return SymVal(sp.simplify(sp.sympify(a) - sp.sympify(b)))
        return SymVal(a - b)

    def __mul__(self, other):
        if isinstance(other, SymVal):
            a = self.v; b = other.v
        else:
            a = self.v; b = other
        if isinstance(a, (sp.Expr, sp.Symbol)) or isinstance(b, (sp.Expr, sp.Symbol)):
            return SymVal(sp.simplify(sp.sympify(a) * sp.sympify(b)))
        return SymVal(a * b)

    def __truediv__(self, other):
        if isinstance(other, SymVal):
            a = self.v; b = other.v
        else:
            a = self.v; b = other
        if isinstance(a, (sp.Expr, sp.Symbol)) or isinstance(b, (sp.Expr, sp.Symbol)):
            return SymVal(sp.simplify(sp.sympify(a) / sp.sympify(b)))
        return SymVal(a / b)

    def __pow__(self, other):
        if isinstance(other, SymVal):
            a = self.v; b = other.v
        else:
            a = self.v; b = other
        if isinstance(a, (sp.Expr, sp.Symbol)) or isinstance(b, (sp.Expr, sp.Symbol)):
            return SymVal(sp.simplify(sp.sympify(a) ** sp.sympify(b)))
        return SymVal(a ** b)

    def __repr__(self):
        return f"SymVal({repr(self.v)})"

    def to_python(self):
        return self.v

# -----------------------
# Environment
# -----------------------
class Environment:
    def __init__(self, parent: Optional["Environment"] = None):
        self.vars: Dict[str, Any] = {}
        self.parent = parent
        self.classes: Dict[str, Dict] = {}

    def get(self, name: str):
        if name in self.vars:
            return self.vars[name]
        if self.parent:
            return self.parent.get(name)
        raise NameError(f"Variable '{name}' no está definida")

    def set(self, name: str, value: Any):
        self.vars[name] = value

    def has(self, name: str) -> bool:
        if name in self.vars:
            return True
        if self.parent:
            return self.parent.has(name)
        return False

    def define_class(self, name: str, class_node: Dict):
        self.classes[name] = class_node

    def get_class(self, name: str):
        if name in self.classes:
            return self.classes[name]
        if self.parent:
            return self.parent.get_class(name)
        raise NameError(f"Clase '{name}' no definida")

# -----------------------
# Interpreter
# -----------------------
class Interpreter:
    def __init__(self, ast: Dict, tracer=None, symbolic: bool = True):
        self.ast = ast
        self.tracer = tracer
        self.symbolic = symbolic

        # Metrics
        self.op_count = 0
        self.loop_stats: List[Dict] = []
        self.call_stack = []
        self.recursion_info: Dict[str, Dict] = {}
        self.max_recursion_depth = 0
        self.current_recursion_depth = 0
        self.trace: List[Tuple[Dict, Dict]] = []
        self.n = sp.Symbol('n', integer=True, positive=True)

        self.procedures = {}
        self.global_env = Environment()
        self._prepare_env()

    def _infer_while_iterations(self, cond_node: Dict, body_node: Dict, env: Environment):
        """Intenta inferir el número de iteraciones de un bucle while."""
        if not self.symbolic:
            return 0  # En modo concreto, no necesitamos la inferencia

        # Lógica simplificada de inferencia:
        # Buscar variables de conteo que tiendan a modificar la condición.
        # Por ahora, se retorna una variable simbólica 'n' o 0.

        # La implementación completa requeriría análisis de terminación y SMT.
        # Como un placeholder funcional, asumimos O(n) si no podemos probar O(1).
        
        # Una mejor aproximación sería:
        # 1. Analizar si la condición incluye 'n'.
        # 2. Analizar si alguna variable en la condición es modificada en el cuerpo.
        # Por simplicidad, retornaremos 'n' si 'n' está definida globalmente.
        
        if env.has("n"):
            return self.n
            
        return 0

    def _prepare_env(self):
        for c in self.ast.get("classes", []):
            self.global_env.define_class(c["name"], c)
        for p in self.ast.get("procedures", []):
            self.procedures[p["name"]] = p
        for g in self.ast.get("graphs", []):
            self.global_env.set(g["name"], {
                "type": "graph",
                "nodos": g.get("nodos"),
                "aristas": g.get("aristas"),
                "pesos": g.get("pesos"),
                "dirigido": g.get("dirigido", False)
            })

    def run(self):
        entry_body = self.ast.get("body", [])
        if isinstance(entry_body, dict) and entry_body.get("type") == "block":
            self.exec_block(entry_body, self.global_env)
        else:
            self.exec_block({"type": "block", "body": entry_body}, self.global_env)

# src/interprete.py (Dentro de la clase Interpreter)

    def eval_array_literal(self, node: Dict, env: Environment) -> List[Any]:
        """Evalúa un nodo AST de tipo 'array_literal' a una lista de Python."""
        elements = []
        
        # Evaluar cada expresión dentro del literal
        for element_node in node.get("elements", []):
            # Es fundamental que cada elemento se evalúe recursivamente
            value = self.eval_expr(element_node, env)
            elements.append(value)
            
        # Devolver una lista de Python, que será el valor del array
        return elements

    def _snapshot_env(self, env: Environment):
        snap = {}
        for k, v in env.vars.items():
            if isinstance(v, list):
                snap[k] = v
            elif isinstance(v, dict) and "__sym_len__" in v:
                snap[k] = f"<array symbolic len={v['__sym_len__']}>"
            else:
                snap[k] = repr(v) if not isinstance(v, (SymVal, sp.Expr, sp.Symbol)) else str(v)
        return snap

    def _count_op(self, k=1):
        self.op_count += k

    def _before(self, node, env):
        if self.tracer:
            try:
                # USAR EXPLÍCITAMENTE LA LÍNEA DEL NODO
                self.tracer.before(node, self._snapshot_env(env), line=node.get("line")) 
            except Exception:
                pass
        self.trace.append((node, self._snapshot_env(env)))

    def _after(self, node, env):
        if self.tracer:
            try:
                self.tracer.after(node, self._snapshot_env(env))
            except Exception:
                pass

    def exec_block(self, block_node: Dict, env: Environment):
        if block_node is None:
            return
        if isinstance(block_node, dict) and block_node.get("type") == "block":
            stmts = block_node.get("body", [])
        elif isinstance(block_node, list):
            stmts = block_node
        else:
            raise RuntimeError("Bloque inválido")

        for stmt in stmts:
            try:
                self.exec_stmt(stmt, env)
            except (BreakSignal, ContinueSignal, ReturnSignal):
                raise

    def exec_stmt(self, node: Dict, env: Environment):
        self._before(node, env)
        t = node.get("type")

        try:
            if t == "block":
                self.exec_block(node, env)
                return

            if t == "var_decl":
                name = node["name"]
                if not env.has(name):
                    env.set(name, None)

            elif t == "array_decl":
                dims = node.get("dims", [])
                if dims:
                    first = dims[0]
                    if first["type"] == "size":
                        val_expr = self.eval_expr(first["value"], env)
                        if isinstance(val_expr, (sp.Expr, sp.Symbol)) and self.symbolic:
                            env.set(node["name"], {"__sym_len__": val_expr, "__values__": []})
                        else:
                            size_int = int(val_expr)
                            env.set(node["name"], [None] * (size_int + 1))
                        self._count_op(1)
                    elif first["type"] == "range":
                        start = self.eval_expr(first["start"], env)
                        end = self.eval_expr(first["end"], env)
                        if (isinstance(start, (sp.Expr, sp.Symbol)) or isinstance(end, (sp.Expr, sp.Symbol))) and self.symbolic:
                            size = sp.simplify(end - start + 1)
                            env.set(node["name"], {"__sym_len__": size, "__values__": []})
                        else:
                            size_int = int(end) - int(start) + 1
                            env.set(node["name"], [None] * (size_int + 1))
                        self._count_op(2)
                else:
                    env.set(node["name"], [])

            elif t == "object_decl":
                cname = node.get("class_name")
                obj_name = node.get("name")
                cls_node = env.get_class(cname)
                attributes = cls_node.get("attributes", [])
                inst = {attr: None for attr in attributes}
                inst["__class__"] = cname
                env.set(obj_name, inst)
                self._count_op(1)

            elif t == "assign":
                target = node["target"]
                value = self.eval_expr(node["expr"], env)
                self._count_op(1)

                if target["type"] == "var":
                    name = target["value"]
                    existing = env.vars.get(name)
                    if isinstance(existing, Ref):
                        existing.set(value)
                    else:
                        env.set(name, value)

                elif target["type"] == "field_access":
                    obj_node = target["object"]
                    if obj_node["type"] == "var":
                        obj = env.get(obj_node["value"])
                    else:
                        obj = self.eval_expr(obj_node, env)
                    fld = target["field"]
                    if isinstance(obj, dict):
                        obj[fld] = value
                    else:
                        raise RuntimeError("Acceso a campo en no-objeto")

                elif target["type"] == "array_access":
                    self._handle_array_assign(target, value, env)

                elif target["type"] == "array_range":
                    arr_node = target["array"]
                    start = self.eval_expr(target["start"], env)
                    end = self.eval_expr(target["end"], env)
                    arr = self.eval_expr(arr_node, env)
                    if isinstance(arr, dict) and "__values__" in arr:
                        arr["__slices__"] = arr.get("__slices__", []) + [("assign", start, end, value)]
                    elif isinstance(arr, list):
                        s = int(start) if not isinstance(start, (sp.Expr, sp.Symbol)) else None
                        e = int(end) if not isinstance(end, (sp.Expr, sp.Symbol)) else None
                        if s is None or e is None:
                            raise RuntimeError("Slice simbólico en arreglo concreto no soportado")
                        arr[s:e+1] = value

            elif t == "if":
                cond = self.eval_expr(node["cond"], env)
                self._count_op(1)
                if cond:
                    self.exec_block(node["then"], env)
                else:
                    if node.get("else"):
                        self.exec_block(node["else"], env)

            elif t == "while":
                self._exec_while(node, env)

            elif t == "repeat":
                self._exec_repeat(node, env)

            elif t == "for":
                self._exec_for(node, env)

            elif t == "call":
                self.exec_call(node, env)

            elif t == "return":
                val = self.eval_expr(node.get("expr"), env)
                raise ReturnSignal(val)

            elif t == "break":
                raise BreakSignal()

            elif t == "continue":
                raise ContinueSignal()

            elif t == "class_def":
                env.define_class(node["name"], node)

            elif t == "graph_decl":
                env.set(node["name"], {
                    "type": "graph",
                    "nodos": node.get("nodos"),
                    "aristas": node.get("aristas"),
                    "pesos": node.get("pesos"),
                    "dirigido": node.get("dirigido", False)
                })

            else:
                raise RuntimeError(f"Stmt type not supported: {t}")

        finally:
            self._after(node, env)

    def _handle_array_assign(self, target, value, env):
        """Maneja asignación a array[index]"""
        arr_node = target["array"]
        if arr_node["type"] == "var":
            arr_name = arr_node["value"]
            try:
                arr = env.get(arr_name)
            except NameError:
                arr = []
                env.set(arr_name, arr)
            
            idx = self.eval_expr(target["index"], env)
            
            if isinstance(arr, dict) and "__sym_len__" in arr:
                arr_vals = arr["__values__"]
                if isinstance(idx, (sp.Expr, sp.Symbol)) and self.symbolic:
                    arr_vals.append(("sym_index", idx, value))
                else:
                    i = int(idx)
                    while len(arr_vals) <= i:
                        arr_vals.append(None)
                    arr_vals[i] = value
            else:
                if isinstance(idx, (sp.Expr, sp.Symbol)) and self.symbolic:
                    raise RuntimeError("Index simbólico en arreglo concreto.")
                i = int(idx)
                while len(arr) <= i:
                    arr.append(None)
                arr[i] = value
        else:
            arr = self.eval_expr(arr_node, env)
            idx = self.eval_expr(target["index"], env)
            if isinstance(arr, list):
                arr[int(idx)] = value
            elif isinstance(arr, dict) and "__values__" in arr:
                arr_vals = arr["__values__"]
                if isinstance(idx, (sp.Expr, sp.Symbol)) and self.symbolic:
                    arr_vals.append(("sym_index", idx, value))
                else:
                    i = int(idx)
                    while len(arr_vals) <= i:
                        arr_vals.append(None)
                    arr_vals[i] = value

    def _exec_while(self, node, env):
        """Ejecuta while loop"""
        cond_node = node["cond"]
        iter_expr = self._infer_while_iterations(cond_node, node["body"], env)
        
        body_ops_before = self.op_count
        iterations = 0
        
        while self.eval_expr(node["cond"], env):
            self._count_op(1)  # evaluación condición
            iterations += 1
            try:
                self.exec_block(node["body"], env)
            except ContinueSignal:
                continue
            except BreakSignal:
                break
        
        self._count_op(1)  # última evaluación (falsa)
        
        body_ops_after = self.op_count
        exec_body_ops = body_ops_after - body_ops_before
        
        self.loop_stats.append({
            "type": "while",
            "node": node,
            "iterations": iter_expr,
            "concrete_iterations": iterations,
            "body_ops": exec_body_ops,
            "total_ops": exec_body_ops
        })

    def _exec_repeat(self, node, env):
        """Ejecuta repeat-until loop"""
        
        is_symbolic_cond = isinstance(self.eval_expr(node["cond"], env), (sp.Expr, sp.Symbol))
        
        if self.symbolic and is_symbolic_cond:
            # MODO SIMBÓLICO: solo registrar el bucle y omitir la ejecución.
            iterations = self.n # Asumimos n iteraciones simbólicas
            exec_body_ops = 0
            concrete_iterations = 0
        else:
            # MODO CONCRETO: ejecutar el bucle.
            body_ops_before = self.op_count
            iterations = 0
            
            while True:
                iterations += 1
                try:
                    self.exec_block(node["body"], env)
                except ContinueSignal:
                    pass
                except BreakSignal:
                    break
                
                cond_val = self.eval_expr(node["cond"], env)
                self._count_op(1) 
                
                if cond_val:
                    break
            
            body_ops_after = self.op_count
            exec_body_ops = body_ops_after - body_ops_before
            concrete_iterations = iterations
            iterations = concrete_iterations # Si es concreto, 'iterations' es el conteo real
            
        self.loop_stats.append({
            "type": "repeat",
            "node": node,
            "iterations": iterations,
            "concrete_iterations": concrete_iterations,
            "body_ops": exec_body_ops,
            "total_ops": exec_body_ops
        })

    def _exec_for(self, node, env):
        """Ejecuta for loop"""
        varname = node.get("var") if isinstance(node.get("var"), str) else node["var"]["value"]
        start = self.eval_expr(node["start"], env)
        end = self.eval_expr(node["end"], env)

        is_symbolic_bound = isinstance(start, (sp.Expr, sp.Symbol)) or isinstance(end, (sp.Expr, sp.Symbol))
        
        if self.symbolic and is_symbolic_bound:
            # MODO SIMBÓLICO: solo calcular iter_count y omitir la ejecución del cuerpo.
            iter_count = sp.simplify(end - start + 1)
            concrete_iterations = 0
            exec_body_ops = 0
            control_ops = 0 # No hay operaciones de control concretas
        else:
            # MODO CONCRETO: ejecutar el bucle.
            start_int = int(start)
            end_int = int(end)
            iter_count = end_int - start_int + 1

            self._count_op(1)
            env.set(varname, start_int)

            body_ops_before = self.op_count
            concrete_iterations = 0
            
            for i in range(start_int, end_int + 1):
                self._count_op(1)
                env.set(varname, i)
                concrete_iterations += 1
                
                try:
                    self.exec_block(node["body"], env)
                except ContinueSignal:
                    pass
                except BreakSignal:
                    break
                
                self._count_op(1)
            
            self._count_op(1)
            
            body_ops_after = self.op_count
            exec_body_ops = body_ops_after - body_ops_before
            control_ops = 2 * concrete_iterations + 2 # Init, Last Cmp + (Cmp + Inc) * Iters
        
        self.loop_stats.append({
            "type": "for",
            "node": node,
            "iterations": iter_count,
            "concrete_iterations": concrete_iterations,
            "body_ops": exec_body_ops,
            "control_ops": control_ops,
            "total_ops": exec_body_ops
        })

    def exec_call(self, node: Dict, env: Environment):
        name = node.get("name")
        args = node.get("args", [])
        
        for arg in args:
            self.eval_expr(arg, env)
        
        if name not in self.procedures:
            if name.lower() == "length":
                arg = args[0]
                val = self.eval_expr(arg, env)
                self._count_op(1)
                if isinstance(val, dict) and "__sym_len__" in val and self.symbolic:
                    return val["__sym_len__"]
                if isinstance(val, list):
                    return len(val) - 1 if (len(val) >= 1) else 0
                return 0
            raise RuntimeError(f"Procedimiento '{name}' no definido")

        self._count_op(1)  # llamada

        proc = self.procedures[name]
        params = proc.get("params", [])
        body = proc.get("body")

        new_env = Environment(parent=env)
        for p_node, a_node in zip(params, args):
            if p_node.get("type") == "array_param":
                val = self.eval_expr(a_node, env)
                new_env.set(p_node.get("name"), val)
            elif p_node.get("type") == "object_param":
                val = self.eval_expr(a_node, env)
                new_env.set(p_node.get("name"), val)
            else:
                pname = p_node.get("name")
                if p_node.get("by_ref", False) and a_node.get("type") == "var":
                    ref = Ref(env, a_node["value"])
                    new_env.set(pname, ref)
                else:
                    new_env.set(pname, self.eval_expr(a_node, env))

        is_recursive = self._is_recursive_call(name, proc)
        if is_recursive:
            info = self.recursion_info.get(name, {
                "is_recursive": True,
                "call_count": 0,
                "has_combining_work": False,
                "subproblem": None,
                "depth_pattern": None
            })
            info["call_count"] += 1
            self.recursion_info[name] = info
            self.current_recursion_depth += 1
            self.max_recursion_depth = max(self.max_recursion_depth, self.current_recursion_depth)

        if isinstance(body, dict) and body.get("type") == "block":
            exec_body = body
        elif isinstance(body, list):
            exec_body = body
        else:
            exec_body = [body]

        try:
            self.exec_block(exec_body, new_env)
        except ReturnSignal as r:
            result = r.value
        else:
            result = None

        if is_recursive:
            self.current_recursion_depth -= 1
            self._infer_recursion_pattern(name, proc)
        
        return result

    # CONTINÚA EN EL SIGUIENTE ARCHIVO...
    # CONTINUACIÓN DEL INTÉRPRETE (pegar después de exec_call)

    def _is_recursive_call(self, proc_name: str, proc_node: Dict) -> bool:
        found = False
        def scan(node):
            nonlocal found
            if isinstance(node, dict):
                if node.get("type") == "call" and node.get("name") == proc_name:
                    found = True
                    return
                for v in node.values():
                    if isinstance(v, (dict, list)) and not found:
                        scan(v)
            elif isinstance(node, list):
                for it in node:
                    if not found:
                        scan(it)
        scan(proc_node.get("body", []))
        return found

    def _infer_recursion_pattern(self, proc_name: str, proc_node: Dict):
        info = self.recursion_info.get(proc_name, {
            "is_recursive": True,
            "call_count": 0,
            "has_combining_work": False,
            "subproblem": None,
            "depth_pattern": None
        })
        
        calls = []
        def scan(node):
            if isinstance(node, dict):
                if node.get("type") == "call" and node.get("name") == proc_name:
                    calls.append(node)
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        scan(v)
            elif isinstance(node, list):
                for it in node:
                    scan(it)
        scan(proc_node.get("body", []))
        
        info["call_count"] = max(info.get("call_count", 0), len(calls))
        
        sub = None
        for c in calls:
            for arg in c.get("args", []):
                if arg.get("type") == "binop":
                    op = arg.get("op")
                    left = arg.get("left")
                    right = arg.get("right")
                    if left.get("type") == "var" and left.get("value") == "n" and op in ("MINUS", "MINUS_TOKEN", "MINUS_OP"):
                        sub = "n-1"
                    if left.get("type") == "var" and left.get("value") == "n" and op in ("DIV", "DIV_INT", "DIV_TOKEN"):
                        sub = "n/2"
                if arg.get("type") == "array_range":
                    sub = "slice"
        
        def has_merge(node):
            if isinstance(node, dict):
                if node.get("type") in ("for", "while", "repeat"):
                    return True
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        if has_merge(v):
                            return True
            elif isinstance(node, list):
                for it in node:
                    if has_merge(it):
                        return True
            return False
        
        info["has_combining_work"] = has_merge(proc_node.get("body", []))
        
        if info["call_count"] <= 1 and sub == "n-1":
            info["depth_pattern"] = "linear"
        elif info["call_count"] >= 2 and sub in ("n/2", "slice"):
            info["depth_pattern"] = "tree"
        elif info["call_count"] == 1 and sub == "n/2":
            info["depth_pattern"] = "log"
        else:
            info["depth_pattern"] = "unknown"
        
        info["subproblem"] = sub
        self.recursion_info[proc_name] = info

    # -----------------------
    # Expressions
    # -----------------------
    # -----------------------
    # Expressions
    # -----------------------
    def eval_expr(self, node: Dict, env: Environment):
        if node is None:
            return None
        
        t = node.get("type")
        
        if t == "number":
            return node["value"]
        if t == "string":
            return node["value"]
        if t in ("boolean", "bool"):
            return node.get("value")
        if t == "null":
            return None
        if t == "array_literal":
            return self.eval_array_literal(node, env)
        if t == "var":
            name = node["value"]
            self._count_op(1)
            try:
                val = env.get(name)
            except NameError:
                if name == "n" and self.symbolic:
                    return self.n
                raise
            if isinstance(val, Ref):
                return val.get()
            return val

        if t == "field_access":
            obj_node = node["object"]
            if obj_node.get("type") == "var":
                obj = env.get(obj_node["value"])
            else:
                obj = self.eval_expr(obj_node, env)
            self._count_op(1)
            if isinstance(obj, dict):
                return obj.get(node["field"])
            raise RuntimeError("Acceso a campo en valor no-objeto")

        if t == "array_access":
            arr_node = node["array"]
            arr = self.eval_expr(arr_node, env) if arr_node.get("type") != "var" else env.get(arr_node["value"])
            idx = self.eval_expr(node["index"], env)
            self._count_op(1)
            
            if isinstance(arr, dict) and "__sym_len__" in arr:
                vals = arr["__values__"]
                if isinstance(idx, (sp.Expr, sp.Symbol)) and self.symbolic:
                    # No podemos obtener el valor si el índice es simbólico
                    return None
                return vals[int(idx)] if int(idx) < len(vals) else None
            if isinstance(arr, list):
                if isinstance(idx, (sp.Expr, sp.Symbol)) and self.symbolic:
                    raise RuntimeError("Index simbólico en arreglo concreto no soportado")
                i = int(idx)
                if i < 0 or i >= len(arr):
                    raise RuntimeError("Índice fuera de rango")
                return arr[i]
            raise RuntimeError("Acceso a arreglo inválido")

        if t == "array_range":
            arr = self.eval_expr(node["array"], env)
            s = self.eval_expr(node["start"], env)
            e = self.eval_expr(node["end"], env)
            self._count_op(1)
            if isinstance(arr, list):
                if (isinstance(s, (sp.Expr, sp.Symbol)) or isinstance(e, (sp.Expr, sp.Symbol))) and self.symbolic:
                    # En modo simbólico, representamos un slice sin ejecutarlo
                    return {"__sym_slice__": (s, e), "__values__": []}
                return arr[int(s):int(e)+1]
            if isinstance(arr, dict) and "__values__" in arr:
                return {"__sym_slice__": (s, e), "__values__": []}
            raise RuntimeError("Slice en no-arreglo")

        if t == "string_func":
            fname = node.get("func")
            args = [self.eval_expr(a, env) for a in node.get("args", [])]
            self._count_op(1)
            
            if fname == "length":
                arg = args[0]
                if isinstance(arg, dict) and "__sym_len__" in arg and self.symbolic:
                    return arg["__sym_len__"]
                if isinstance(arg, list):
                    return len(arg)-1 if len(arg) >=1 else 0
                if isinstance(arg, str):
                    return len(arg)
                return 0
            if fname == "upper":
                return args[0].upper() if args[0] is not None else None
            if fname == "lower":
                return args[0].lower() if args[0] is not None else None
            if fname == "trim":
                return args[0].strip() if args[0] is not None else None
            if fname == "substring":
                s = args[1]
                e = args[2]
                return args[0][int(s):int(e)+1] if isinstance(args[0], str) else None

        if t == "ceil":
            val = self.eval_expr(node["expr"], env)
            self._count_op(1)
            if isinstance(val, (sp.Expr, sp.Symbol)) and self.symbolic:
                return sp.ceiling(val)
            return math.ceil(val)
        
        if t == "floor":
            val = self.eval_expr(node["expr"], env)
            self._count_op(1)
            if isinstance(val, (sp.Expr, sp.Symbol)) and self.symbolic:
                return sp.floor(val)
            return math.floor(val)

        if t in ("call", "call_expr"):  # <--- ADAPTACIÓN AQUÍ
            # exec_call maneja la lógica de ejecución y devuelve el resultado
            return self.exec_call(node, env)

        if t in ("binop", "binary"):
            op = node.get("op")
            left = self.eval_expr(node.get("left"), env)
            right = self.eval_expr(node.get("right"), env)
            self._count_op(1)
            
            is_symbolic = (self.symbolic and 
                        (isinstance(left, (sp.Expr, sp.Symbol)) or isinstance(right, (sp.Expr, sp.Symbol))))
            
            if is_symbolic:
                L = sp.sympify(left) if not isinstance(left, (sp.Expr, sp.Symbol)) else left
                R = sp.sympify(right) if not isinstance(right, (sp.Expr, sp.Symbol)) else right
                
                if op in ("PLUS", "PLUS_TOKEN", "PLUS_OP"):
                    return sp.simplify(L + R)
                if op in ("MINUS", "MINUS_TOKEN", "MINUS_OP"):
                    return sp.simplify(L - R)
                if op in ("MULT", "TIMES", "STAR"):
                    return sp.simplify(L * R)
                if op in ("DIV", "DIV_FLOAT", "DIV_TOKEN"):
                    return sp.simplify(L / R)
                if op in ("DIV_INT", "DIV_INT_TOKEN"):
                    return sp.floor(L / R)
                if op in ("MOD",):
                    return sp.Mod(L, R)
                if op in ("POW", "EXP", "STAR_STAR"):
                    return sp.simplify(L ** R)
                if op in ("GT",):
                    return L > R
                if op in ("LT",):
                    return L < R
                if op in ("GE",):
                    return L >= R
                if op in ("LE",):
                    return L <= R
                if op in ("EQ",):
                    return sp.Eq(L, R)
                if op in ("NE",):
                    return sp.Ne(L, R)
                if op in ("AND",):
                    return sp.And(L, R)
                if op in ("OR",):
                    return sp.Or(L, R)
            
            # Modo concreto
            
            # --- ADAPTACIÓN CLAVE PARA ELIMINAR EL TypeError: NoneType and int ---
            # Si una variable no fue inicializada, su valor es None. En operaciones matemáticas, 
            # asumimos que debe comportarse como 0.
            if left is None:
                left = 0
            if right is None:
                right = 0
            # ----------------------------------------------------------------------
            
            if op in ("PLUS", "PLUS_TOKEN", "PLUS_OP"):
                return left + right
            if op in ("MINUS", "MINUS_TOKEN", "MINUS_OP"):
                return left - right
            if op in ("MULT", "TIMES", "STAR"):
                return left * right
            if op in ("DIV", "DIV_FLOAT", "DIV_TOKEN"):
                return left / right
            if op in ("DIV_INT", "DIV_INT_TOKEN"):
                return left // right
            if op in ("MOD",):
                return left % right
            if op in ("POW", "EXP", "STAR_STAR"):
                return left ** right
            if op in ("GT",):
                return left > right
            if op in ("LT",):
                return left < right
            if op in ("GE",):
                return left >= right
            if op in ("LE",):
                return left <= right
            if op in ("EQ",):
                return left == right
            if op in ("NE",):
                return left != right
            if op in ("AND",):
                return left and right
            if op in ("OR",):
                return left or right
            
            raise RuntimeError(f"Operador binario no soportado: {op}")

        if t in ("unary", "unop", "unaryop"):
            op = node.get("op")
            expr = self.eval_expr(node.get("operand") or node.get("expr"), env)
            self._count_op(1)
            
            is_symbolic = (self.symbolic and isinstance(expr, (sp.Expr, sp.Symbol)))

            if op in ("MINUS", "NEG"):
                if is_symbolic:
                    return -expr
                return -expr
            
            if op in ("NOT", "NEGATION", "EXCLAMATION"):
                if is_symbolic:
                    return sp.Not(expr)
                return not expr
            
            raise RuntimeError(f"Operador unario no soportado: {op}")
            
        raise RuntimeError(f"Expr type not supported: {t}")

    def _infer_while_iterations(self, cond_node: Dict, body_node: Dict, env: Environment):
        if not isinstance(cond_node, dict):
            return self.n if self.symbolic else 0
        
        if cond_node.get("type") == "binop":
            left = cond_node.get("left")
            right = cond_node.get("right")
            
            if left and left.get("type") == "var" and ((right.get("type") == "var" and right.get("value") == "n") or isinstance(self.eval_expr(right, env), (sp.Expr, sp.Symbol))):
                upd = self._find_variable_modification(body_node, left.get("value"))
                if upd:
                    op = upd.get("op")
                    val = upd.get("value")
                    if op in ("+", "PLUS", "MINUS"):
                        return self.n
                    if op in ("*", "MULT", "TIMES"):
                        return sp.log(self.n, int(val)) if self.symbolic and val.isdigit() else sp.log(self.n)
        
        return self.n if self.symbolic else 0

    def _find_variable_modification(self, body_node, var_name):
        found = None
        def scan(node):
            nonlocal found
            if found:
                return
            if isinstance(node, dict):
                t = node.get("type")
                if t == "assign":
                    target = node.get("target")
                    if target.get("type") == "var" and target.get("value") == var_name:
                        expr = node.get("expr")
                        if expr and expr.get("type") in ("binop", "binary"):
                            op = expr.get("op")
                            left = expr.get("left")
                            right = expr.get("right")
                            
                            if left.get("type") == "var" and left.get("value") == var_name:
                                other = right
                            elif right.get("type") == "var" and right.get("value") == var_name:
                                other = left
                            else:
                                other = None
                            
                            val = None
                            if other:
                                if other.get("type") == "number":
                                    val = other.get("value")
                                elif other.get("type") == "var" and other.get("value") == "n":
                                    val = "n"
                            found = {"op": op, "value": val}
                            return
                for v in node.values():
                    if isinstance(v, (dict, list)):
                        scan(v)
            elif isinstance(node, list):
                for it in node:
                    scan(it)
        scan(body_node)
        return found

    def get_metrics(self) -> Dict:
        return {
            "op_count": self.op_count,
            "loop_stats": self.loop_stats,
            "recursion_info": self.recursion_info,
            "max_recursion_depth": self.max_recursion_depth,
            "trace_len": len(self.trace)
        }

    def get_recursion_info(self):
        return self.recursion_info

    def get_trace(self):
        return self.trace