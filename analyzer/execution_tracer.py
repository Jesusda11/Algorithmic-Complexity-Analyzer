# interpreter/execution_tracer.py
from typing import Any, Dict, List, Optional
import copy

class ExecutionStep:
    """Representa un paso de ejecución con toda su información"""
    def __init__(self, step_id: int, node: Dict, action: str, env_snapshot: Dict, 
                 call_stack: List[str], line: int, col: int):
        self.step_id = step_id
        self.node = node
        self.action = action
        self.env_snapshot = env_snapshot
        self.call_stack = call_stack.copy()
        self.line = line
        self.col = col
        self.result = None
        self.error = None
        
    def to_dict(self):
        return {
            "step_id": self.step_id,
            "action": self.action,
            "node_type": self.node.get("type") if self.node else None,
            "line": self.line,
            "col": self.col,
            "variables": self.env_snapshot,
            "call_stack": self.call_stack,
            "result": str(self.result) if self.result is not None else None,
            "error": self.error
        }


class ExecutionTracer:
    """
    Captura la ejecución línea por línea para visualización en el frontend.
    Genera un árbol de ejecución con estados de variables y call stack.
    """
    
    def __init__(self):
        self.steps: List[ExecutionStep] = []
        self.step_counter = 0
        self.current_call_stack: List[str] = ["<main>"]
        self.scope_tree = {
            "name": "<main>",
            "type": "main",
            "children": [],
            "steps": []
        }
        self.current_scope = self.scope_tree
        self.scope_stack = [self.scope_tree]
        
    def capture_step(self, node: Dict, action: str, env_snapshot: Dict, 
                     line: int = None, col: int = None, result=None):
        """Captura un paso de ejecución"""
        if line is None and node:
            line = node.get("line", 0)
        if col is None and node:
            col = node.get("col", 0)
            
        step = ExecutionStep(
            step_id=self.step_counter,
            node=node,
            action=action,
            env_snapshot=copy.deepcopy(env_snapshot),
            call_stack=self.current_call_stack.copy(),
            line=line,
            col=col
        )
        step.result = result
        
        self.steps.append(step)
        self.current_scope["steps"].append(self.step_counter)
        self.step_counter += 1
        
        return step
    
    def enter_scope(self, scope_name: str, scope_type: str, node: Dict = None):
        """Entra a un nuevo scope (función, loop, bloque)"""
        new_scope = {
            "name": scope_name,
            "type": scope_type,
            "node": node,
            "children": [],
            "steps": [],
            "start_step": self.step_counter
        }
        
        self.current_scope["children"].append(new_scope)
        self.scope_stack.append(new_scope)
        self.current_scope = new_scope
        
        if scope_type == "procedure":
            self.current_call_stack.append(scope_name)
    
    def exit_scope(self, scope_type: str = None):
        """Sale del scope actual"""
        if len(self.scope_stack) > 1:
            exiting = self.scope_stack.pop()
            exiting["end_step"] = self.step_counter - 1
            self.current_scope = self.scope_stack[-1]
            
            if scope_type == "procedure" and len(self.current_call_stack) > 1:
                self.current_call_stack.pop()
    
    def get_execution_tree(self):
        """Retorna el árbol completo de ejecución"""
        return {
            "scope_tree": self.scope_tree,
            "total_steps": self.step_counter,
            "steps": [step.to_dict() for step in self.steps]
        }
    
    def get_step(self, step_id: int):
        """Obtiene un paso específico por ID"""
        if 0 <= step_id < len(self.steps):
            return self.steps[step_id].to_dict()
        return None
    
    def get_steps_by_line(self, line: int):
        """Obtiene todos los pasos ejecutados en una línea específica"""
        return [step.to_dict() for step in self.steps if step.line == line]
    
    def get_variable_history(self, var_name: str):
        """Rastrea el historial de cambios de una variable"""
        history = []
        for step in self.steps:
            if var_name in step.env_snapshot:
                history.append({
                    "step_id": step.step_id,
                    "line": step.line,
                    "value": step.env_snapshot[var_name],
                    "action": step.action
                })
        return history
    
    def get_call_stack_at_step(self, step_id: int):
        """Obtiene el call stack en un paso específico"""
        if 0 <= step_id < len(self.steps):
            return self.steps[step_id].call_stack
        return []
    
    def before(self, node: Dict, env_snapshot: Dict):
        """Hook llamado ANTES de ejecutar un nodo"""
        action = f"enter_{node.get('type', 'unknown')}"
        self.capture_step(node, action, env_snapshot)
    
    def after(self, node: Dict, env_snapshot: Dict):
        """Hook llamado DESPUÉS de ejecutar un nodo"""
        action = f"exit_{node.get('type', 'unknown')}"
        self.capture_step(node, action, env_snapshot)
    
    def export_for_frontend(self):
        """
        Exporta toda la información en un formato optimizado para el frontend
        """
        return {
            "execution_tree": self.get_execution_tree(),
            "timeline": [
                {
                    "step": i,
                    "line": step.line,
                    "col": step.col,
                    "action": step.action,
                    "node_type": step.node.get("type") if step.node else None,
                    "variables": step.env_snapshot,
                    "call_stack": step.call_stack,
                    "scope_depth": len(step.call_stack)
                }
                for i, step in enumerate(self.steps)
            ],
            "line_execution_count": self._get_line_execution_counts(),
            "variable_lifetimes": self._get_variable_lifetimes()
        }
    
    def _get_line_execution_counts(self):
        """Cuenta cuántas veces se ejecutó cada línea"""
        counts = {}
        for step in self.steps:
            if step.line:
                counts[step.line] = counts.get(step.line, 0) + 1
        return counts
    
    def _get_variable_lifetimes(self):
        """Determina el tiempo de vida de cada variable"""
        lifetimes = {}
        for step in self.steps:
            for var_name in step.env_snapshot:
                if var_name not in lifetimes:
                    lifetimes[var_name] = {
                        "first_seen": step.step_id,
                        "last_seen": step.step_id,
                        "scope": step.call_stack[-1] if step.call_stack else "<main>"
                    }
                else:
                    lifetimes[var_name]["last_seen"] = step.step_id
        return lifetimes


# -----------------------
# Integración con el Interpreter
# -----------------------
def create_traced_interpreter(ast, symbolic=True):
    """
    Factory que crea un intérprete con trazado completo
    """
    # Importar aquí para evitar dependencias circulares
    from analyzer.interprete import Interpreter
    
    tracer = ExecutionTracer()
    interpreter = Interpreter(ast, tracer=tracer, symbolic=symbolic)
    
    # Monkey-patch para capturar eventos adicionales
    original_exec_stmt = interpreter.exec_stmt
    
    def traced_exec_stmt(node, env):
        node_type = node.get("type")
        
        # Capturar entrada a scopes especiales
        if node_type == "for":
            var_name = node.get("var")
            if isinstance(var_name, dict):
                var_name = var_name.get("value", "i")
            tracer.enter_scope(f"for_{var_name}", "for", node)
        elif node_type == "while":
            tracer.enter_scope("while", "while", node)
        elif node_type == "if":
            tracer.enter_scope("if", "if", node)
        elif node_type == "block":
            tracer.enter_scope("block", "block", node)
        
        try:
            result = original_exec_stmt(node, env)
            return result
        finally:
            # Capturar salida de scopes
            if node_type in ("for", "while", "if", "block"):
                tracer.exit_scope(node_type)
    
    interpreter.exec_stmt = traced_exec_stmt
    
    # Monkey-patch para procedures
    original_exec_call = interpreter.exec_call
    
    def traced_exec_call(node, env):
        proc_name = node.get("name")
        tracer.enter_scope(proc_name, "procedure", node)
        try:
            result = original_exec_call(node, env)
            return result
        finally:
            tracer.exit_scope("procedure")
    
    interpreter.exec_call = traced_exec_call
    
    return interpreter, tracer


# -----------------------
# Utilidades para el Frontend
# -----------------------
class ExecutionPlayer:
    """
    Permite reproducir la ejecución paso a paso
    """
    def __init__(self, tracer: ExecutionTracer):
        self.tracer = tracer
        self.current_step = 0
        self.total_steps = len(tracer.steps)
    
    def next_step(self):
        """Avanza al siguiente paso"""
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
        return self.get_current_state()
    
    def prev_step(self):
        """Retrocede al paso anterior"""
        if self.current_step > 0:
            self.current_step -= 1
        return self.get_current_state()
    
    def jump_to_step(self, step_id: int):
        """Salta a un paso específico"""
        if 0 <= step_id < self.total_steps:
            self.current_step = step_id
        return self.get_current_state()
    
    def jump_to_line(self, line: int):
        """Salta a la próxima ejecución de una línea"""
        for i in range(self.current_step + 1, self.total_steps):
            if self.tracer.steps[i].line == line:
                self.current_step = i
                return self.get_current_state()
        return None
    
    def get_current_state(self):
        """Obtiene el estado actual completo"""
        if self.current_step < self.total_steps:
            step = self.tracer.steps[self.current_step]
            return {
                "step_id": self.current_step,
                "total_steps": self.total_steps,
                "line": step.line,
                "col": step.col,
                "action": step.action,
                "node_type": step.node.get("type") if step.node else None,
                "variables": step.env_snapshot,
                "call_stack": step.call_stack,
                "can_go_next": self.current_step < self.total_steps - 1,
                "can_go_prev": self.current_step > 0
            }
        return None
    
    def play_until_line(self, target_line: int, max_steps: int = 1000):
        """Ejecuta hasta llegar a una línea específica"""
        steps_taken = 0
        while self.current_step < self.total_steps - 1 and steps_taken < max_steps:
            self.current_step += 1
            steps_taken += 1
            if self.tracer.steps[self.current_step].line == target_line:
                return self.get_current_state()
        return None
    
    def get_breakpoint_lines(self):
        """Obtiene todas las líneas únicas ejecutadas (para breakpoints)"""
        return sorted(set(step.line for step in self.tracer.steps if step.line))