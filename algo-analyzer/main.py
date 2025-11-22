from analyzer.parser import parse_pseudocode
from analyzer.complexity import analyze_complexity

def main():
    # Cargar pseudocódigo de ejemplo
    with open("examples/sample1.txt", "r", encoding="utf-8") as f:
        code = f.read()

    print("=== PSEUDOCÓDIGO ===")
    print(code)
    print("====================\n")

    # PARSER (paso 1)
    structure = parse_pseudocode(code)
    print("Estructura interna mínima:")
    print(structure)

    # ANALIZADOR DE COMPLEJIDAD (paso 2)
    result = analyze_complexity(structure)
    print("\nComplejidad estimada:")
    print(result)


if __name__ == "__main__":
    main()
