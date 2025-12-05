# main.py - Ejemplo completo de uso del intérprete

from lexer.lexer import Lexer
from parser.parser import Parser
from analyzer.interprete import Interpreter
from analyzer.execution_tracer import ExecutionTracer, ExecutionPlayer, create_traced_interpreter
import json

# ==================================================
# EJEMPLO 1: Bubble Sort Simple
# ==================================================
BUBBLE_SORT = """
PROCEDURE ContarDigitos(N, Contador)
BEGIN
    IF (N < 0) THEN
    BEGIN

    END
    ELSE
    BEGIN
        Contador 🡨 Contador + 1
        CALL ContarDigitos(N / 10, Contador)
    END
END

BEGIN
    VAR Numero 🡨 12345
    VAR Conteo 🡨 0 

    CALL ContarDigitos(Numero, Conteo) 
END
"""

# ==================================================
# EJEMPLO 2: Suma de Array
# ==================================================
SUM_ARRAY = """
► Suma de elementos de un array
n 🡨 10
A[10]
suma 🡨 0

► Llenar array
for i 🡨 1 to n do
begin
    A[i] 🡨 i
end

► Sumar elementos
for i 🡨 1 to n do
begin
    suma 🡨 suma + A[i]
end
"""

# ==================================================
# EJEMPLO 3: Búsqueda Lineal
# ==================================================
LINEAR_SEARCH = """
► Búsqueda lineal
n 🡨 8
A[8]
buscado 🡨 5
encontrado 🡨 F
posicion 🡨 -1

► Llenar array
for i 🡨 1 to n do
begin
    A[i] 🡨 i
end

► Buscar elemento
i 🡨 1
while (i ≤ n and not encontrado) do
begin
    if (A[i] = buscado) then
    begin
        encontrado 🡨 T
        posicion 🡨 i
    end
    i 🡨 i + 1
end
"""

# ==================================================
# EJEMPLO 4: Fibonacci Recursivo
# ==================================================
FIBONACCI = """
procedure fibonacci(n)
begin
    if (n ≤ 1) then
    begin
        return n
    end
    
    a 🡨 call fibonacci(n - 1)
    b 🡨 call fibonacci(n - 2)
    return a + b
end

n 🡨 5
resultado 🡨 call fibonacci(n)
"""

# ==================================================
# EJEMPLO 5: MergeSort (simulado)
# ==================================================
MERGE_SORT = """
procedure mergeSort(A[], inicio, fin)
begin
    if (inicio < fin) then
    begin
        medio 🡨 └(inicio + fin) / 2┘
        
        ► Dividir
        call mergeSort(A, inicio, medio)
        call mergeSort(A, medio + 1, fin)
        
        ► Merge simulado (solo contar operaciones)
        for i 🡨 inicio to fin do
        begin
            temp 🡨 A[i]
        end
    end
end

n 🡨 8
A[8]

for i 🡨 1 to n do
begin
    A[i] 🡨 n - i + 1
end

call mergeSort(A, 1, n)
"""

# ==================================================
# EJEMPLO 6: Matriz (operaciones anidadas)
# ==================================================
MATRIX_OPS = """
► Operaciones con matrices
n 🡨 3
m 🡨 3
A[3][3]
B[3][3]
C[3][3]

► Llenar matrices A y B
for i 🡨 1 to n do
begin
    for j 🡨 1 to m do
    begin
        A[i][j] 🡨 i + j
        B[i][j] 🡨 i * j
    end
end

► Multiplicar C = A * B
for i 🡨 1 to n do
begin
    for j 🡨 1 to m do
    begin
        C[i][j] 🡨 0
        for k 🡨 1 to m do
        begin
            C[i][j] 🡨 C[i][j] + A[i][k] * B[k][j]
        end
    end
end
"""

# ==================================================
# Funciones auxiliares
# ==================================================

def parse_code(code: str):
    """Parsea código pseudocódigo y retorna AST"""
    print("🔍 Lexing...")
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    
    print(f"✅ {len(tokens)} tokens generados")
    
    print("\n🔍 Parsing...")
    parser = Parser(tokens)
    ast = parser.parse()
    
    print("✅ AST generado exitosamente")
    return ast

def run_with_tracer(ast, symbolic=True):
    """Ejecuta con trazado completo"""
    print("\n🚀 Ejecutando con trazado...")
    
    # Crear intérprete con tracer
    interpreter, tracer = create_traced_interpreter(ast, symbolic=symbolic)
    
    # Ejecutar
    try:
        interpreter.run()
        print("✅ Ejecución completada")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, None
    
    return interpreter, tracer

def print_metrics(interpreter):
    """Imprime métricas de complejidad"""
    metrics = interpreter.get_metrics()
    
    print("\n" + "="*60)
    print("📊 MÉTRICAS DE COMPLEJIDAD")
    print("="*60)
    
    print(f"\n🔢 Operaciones totales: {metrics['op_count']}")
    
    if metrics['loop_stats']:
        print("\n🔄 Análisis de Loops:")
        for i, loop in enumerate(metrics['loop_stats'], 1):
            print(f"\n  Loop #{i} ({loop['type']}):")
            print(f"    - Iteraciones: {loop.get('iterations', 'unknown')}")
            print(f"    - Iteraciones concretas: {loop.get('concrete_iterations', 0)}")
            print(f"    - Operaciones del cuerpo: {loop.get('body_ops', 0)}")
            if 'control_ops' in loop:
                print(f"    - Operaciones de control: {loop.get('control_ops', 0)}")
    
    if metrics['recursion_info']:
        print("\n🔁 Análisis de Recursión:")
        for proc_name, info in metrics['recursion_info'].items():
            print(f"\n  Procedimiento: {proc_name}")
            print(f"    - Patrón: {info.get('depth_pattern', 'unknown')}")
            print(f"    - Subproblema: {info.get('subproblem', 'unknown')}")
            print(f"    - Trabajo de combinación: {info.get('has_combining_work', False)}")
            print(f"    - Profundidad máxima: {metrics.get('max_recursion_depth', 0)}")

def print_execution_trace(tracer, max_steps=20):
    """Imprime traza de ejecución"""
    print("\n" + "="*60)
    print("📝 TRAZA DE EJECUCIÓN (primeros pasos)")
    print("="*60)
    
    steps = tracer.steps[:max_steps]
    
    for i, step in enumerate(steps):
        print(f"\n🔸 Paso {step.step_id} (Línea {step.line}):")
        print(f"   Acción: {step.action}")
        print(f"   Call Stack: {' → '.join(step.call_stack)}")
        
        if step.env_snapshot:
            vars_str = ", ".join([f"{k}={v}" for k, v in list(step.env_snapshot.items())[:3]])
            if len(step.env_snapshot) > 3:
                vars_str += f" ... (+{len(step.env_snapshot)-3} más)"
            print(f"   Variables: {vars_str}")
    
    if len(tracer.steps) > max_steps:
        print(f"\n... y {len(tracer.steps) - max_steps} pasos más")

def print_line_heatmap(tracer):
    """Imprime mapa de calor de líneas ejecutadas"""
    print("\n" + "="*60)
    print("🔥 MAPA DE CALOR (líneas más ejecutadas)")
    print("="*60)
    
    line_counts = {}
    for step in tracer.steps:
        if step.line:
            line_counts[step.line] = line_counts.get(step.line, 0) + 1
    
    # Ordenar por frecuencia
    sorted_lines = sorted(line_counts.items(), key=lambda x: x[1], reverse=True)
    
    for line, count in sorted_lines[:10]:
        bar = "█" * min(50, count // max(1, max(line_counts.values()) // 50))
        print(f"  Línea {line:3d}: {bar} ({count} veces)")

def export_to_json(interpreter, tracer, filename="execution_data.json"):
    """Exporta toda la información a JSON para el frontend"""
    execution_data = tracer.export_for_frontend()
    metrics = interpreter.get_metrics()
    
    output = {
        "success": True,
        "execution": {
            "timeline": execution_data["timeline"],
            "scope_tree": execution_data["execution_tree"]["scope_tree"],
            "total_steps": execution_data["execution_tree"]["total_steps"],
            "line_heatmap": execution_data["line_execution_count"],
            "variable_lifetimes": execution_data["variable_lifetimes"]
        },
        "metrics": {
            "total_operations": metrics["op_count"],
            "loops": [
                {
                    "type": loop["type"],
                    "iterations": str(loop.get("iterations", "unknown")),
                    "concrete_iterations": loop.get("concrete_iterations", 0),
                    "body_operations": loop.get("body_ops", 0)
                }
                for loop in metrics.get("loop_stats", [])
            ],
            "recursion": {
                proc_name: {
                    "pattern": info.get("depth_pattern", "unknown"),
                    "subproblem": info.get("subproblem", "unknown"),
                    "has_combining_work": info.get("has_combining_work", False)
                }
                for proc_name, info in metrics.get("recursion_info", {}).items()
            }
        }
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Datos exportados a: {filename}")

def demo_player(tracer):
    """Demo del player paso a paso"""
    print("\n" + "="*60)
    print("🎮 DEMO: Navegación Paso a Paso")
    print("="*60)
    
    player = ExecutionPlayer(tracer)
    
    print("\n▶️  Primeros 5 pasos:")
    for _ in range(5):
        state = player.next_step()
        if state:
            print(f"  Paso {state['step_id']}: Línea {state['line']} - {state['action']}")
    
    print("\n⏮️  Retrocediendo 2 pasos:")
    for _ in range(2):
        state = player.prev_step()
        if state:
            print(f"  Paso {state['step_id']}: Línea {state['line']} - {state['action']}")
    
    print(f"\n📍 Líneas disponibles para breakpoints: {player.get_breakpoint_lines()[:10]}")

# ==================================================
# MAIN
# ==================================================

def main():
    print("="*60)
    print("🚀 ANALIZADOR DE COMPLEJIDAD ALGORÍTMICA")
    print("="*60)
    
    # Seleccionar ejemplo
    ejemplos = {
        "1": ("Bubble Sort", BUBBLE_SORT),
        "2": ("Suma de Array", SUM_ARRAY),
        "3": ("Búsqueda Lineal", LINEAR_SEARCH),
        "4": ("Fibonacci Recursivo", FIBONACCI),
        "5": ("Merge Sort", MERGE_SORT),
        "6": ("Operaciones con Matrices", MATRIX_OPS)
    }
    
    print("\n📚 Ejemplos disponibles:")
    for key, (name, _) in ejemplos.items():
        print(f"  {key}. {name}")
    
    choice = input("\n👉 Selecciona un ejemplo (1-6) [1]: ").strip() or "1"
    
    if choice not in ejemplos:
        print("❌ Opción inválida")
        return
    
    ejemplo_nombre, codigo = ejemplos[choice]
    
    print(f"\n✨ Ejecutando: {ejemplo_nombre}")
    print("-"*60)
    print(codigo[:200] + "..." if len(codigo) > 200 else codigo)
    print("-"*60)
    
    # Parsear
    ast = parse_code(codigo)
    
    # Ejecutar con trazado
    interpreter, tracer = run_with_tracer(ast, symbolic=True)
    
    if not interpreter or not tracer:
        print("\n❌ No se pudo ejecutar el código")
        return
    
    # Mostrar resultados
    print_metrics(interpreter)
    print_execution_trace(tracer, max_steps=15)
    print_line_heatmap(tracer)
    
    # Demo del player
    demo_player(tracer)
    
    # Exportar a JSON
    export_to_json(interpreter, tracer, f"output_{ejemplo_nombre.lower().replace(' ', '_')}.json")
    
    print("\n" + "="*60)
    print("✅ ANÁLISIS COMPLETADO")
    print("="*60)
    
    # Variables finales
    final_env = interpreter.global_env.vars
    if final_env:
        print("\n📋 Variables finales:")
        for var, val in list(final_env.items())[:10]:
            print(f"  {var} = {val}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()