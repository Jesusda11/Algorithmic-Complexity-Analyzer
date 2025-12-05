from lexer.lexer import Lexer
from parser.parser import Parser
from analyzer.interprete import Interpreter, SymVal


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":

    # 1. Leer archivo de ejemplo
    code = read_file("examples/interprete.txt")

    # 2. Lexer → convertir código en tokens
    lexer = Lexer(code)
    tokens = lexer.tokenize()

    print("\n=== TOKENS GENERADOS ===")
    for t in tokens:
        print(t)
    print("=========================\n")

    # 3. Parser → generar AST
    parser = Parser(tokens)
    ast = parser.parse()

    print("=== AST GENERADO ===")
    print(ast)
    print("====================\n")

    # 4. Intérprete → ejecutar AST
    interpreter = Interpreter(ast)
    print("=== EJECUCIÓN DEL PROGRAMA ===")
    interpreter.run()
    print("=== PROGRAMA FINALIZADO ===\n")

    # 5. Mostrar métricas
    metrics = interpreter.get_metrics()
    print("=== MÉTRICAS ===")
    print(f"Conteo de operaciones: {metrics['op_count']}")
    print("Estadísticas de loops:")
    for loop in metrics["loop_stats"]:
        print(f"  Tipo: {loop['type']}, Iteraciones: {loop['iterations']}, Ops en cuerpo: {loop['body_ops']}")
    print(f"Profundidad máxima de recursión: {metrics['max_recursion_depth']}")
    print("Info de recursión por procedimiento:")
    for name, info in metrics["recursion_info"].items():
        print(f"  {name}: {info}")

    # 6. Mostrar último snapshot de variables globales
    print("\n=== VARIABLES GLOBALES FINALES ===")
    for var, val in interpreter.global_env.vars.items():
        # si es SymVal o sympy, simplificar
        if isinstance(val, SymVal):
            val = val.as_sympy()
        print(f"{var} = {val}")
