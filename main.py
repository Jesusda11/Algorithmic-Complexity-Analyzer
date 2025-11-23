import json
import sys
from pathlib import Path

# Imports del proyecto
from lexer.lexer import Lexer
from parser.parser import Parser
from semantic.validator import validate_pseudocode, SemanticError
from analyzer.recursion import RecursionDetector
from analyzer.complexity import ComplexityAnalyzer


def read_file(path):
    """Lee un archivo de pseudocódigo"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{path}'")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
        sys.exit(1)


def print_separator(title="", char="="):
    """Imprime un separador visual"""
    width = 80
    if title:
        print(f"\n{char * width}")
        print(f"{title:^{width}}")
        print(f"{char * width}")
    else:
        print(f"{char * width}")


def print_phase(phase_number, phase_name):
    """Imprime el encabezado de una fase"""
    print_separator(f"FASE {phase_number}: {phase_name.upper()}")


def analyze_pseudocode(filepath, verbose=True, show_ast=False):
    """
    Pipeline completo de análisis de pseudocódigo
    
    Args:
        filepath: Ruta al archivo de pseudocódigo
        verbose: Si True, muestra información detallada
        show_ast: Si True, muestra el AST completo
        
    Returns:
        dict con resultados del análisis
    """
    
    # ========================================
    # CARGAR PSEUDOCÓDIGO
    # ========================================
    if verbose:
        print_separator("ANALIZADOR DE COMPLEJIDAD COMPUTACIONAL")
        print(f"\n📂 Archivo: {filepath}")
    
    code = read_file(filepath)
    
    if verbose:
        print(f"\n📝 Pseudocódigo cargado ({len(code)} caracteres):")
        print("-" * 80)
        print(code[:500] + ("..." if len(code) > 500 else ""))
        print("-" * 80)
    
    try:
        # ========================================
        # FASE 1: ANÁLISIS LÉXICO
        # ========================================
        if verbose:
            print_phase(1, "Análisis Léxico (Tokenización)")
        
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        
        if verbose:
            print(f"✓ Tokens generados: {len(tokens)}")
            # Mostrar primeros 10 tokens
            print("\nPrimeros tokens:")
            for i, tok in enumerate(tokens[:10]):
                print(f"  {i+1:2d}. {tok}")
            if len(tokens) > 10:
                print(f"  ... y {len(tokens) - 10} tokens más")
        
        # ========================================
        # FASE 2: ANÁLISIS SINTÁCTICO
        # ========================================
        if verbose:
            print_phase(2, "Análisis Sintáctico (Parsing)")
        
        parser = Parser(tokens)
        ast = parser.parse()
        
        if verbose:
            print(f"✓ AST generado exitosamente")
            print(f"  - Clases definidas: {len(ast.get('classes', []))}")
            print(f"  - Procedimientos: {len(ast.get('procedures', []))}")
            print(f"  - Statements en body: {len(ast.get('body', []))}")
            
            # Listar procedimientos
            if ast.get('procedures'):
                print("\n  Procedimientos encontrados:")
                for proc in ast['procedures']:
                    params = len(proc.get('params', []))
                    print(f"    • {proc['name']}({params} parámetros)")
        
        if show_ast:
            print("\n📊 AST Completo:")
            print(json.dumps(ast, indent=2, ensure_ascii=False))
        
        # ========================================
        # FASE 3: VALIDACIÓN SEMÁNTICA
        # ========================================
        
        
        # ========================================
        # FASE 4: DETECCIÓN DE RECURSIÓN
        # ========================================
        if verbose:
            print_phase(4, "Detección de Recursión")
        
        detector = RecursionDetector(ast)
        recursion_info = detector.analyze()
        
        if verbose:
            if ast.get('procedures'):
                has_recursion = any(info.is_recursive for info in recursion_info.values())
                
                if has_recursion:
                    print("✓ Recursión detectada:")
                    for proc_name, info in recursion_info.items():
                        if info.is_recursive:
                            print(f"\n  📌 {proc_name}:")
                            print(f"     Tipo: {info.recursion_type}")
                            print(f"     Patrón: {info.depth_pattern}")
                            print(f"     Llamadas: {info.call_count}")
                else:
                    print("✓ No se detectó recursión")
            else:
                print("  (No hay procedimientos para analizar)")
        
        # ========================================
        # FASE 5: ANÁLISIS DE COMPLEJIDAD
        # ========================================
        if verbose:
            print_phase(5, "Análisis de Complejidad")
        
        analyzer = ComplexityAnalyzer(ast, recursion_info)
        complexity = analyzer.analyze()
        
        if verbose:
            print("✓ Análisis completado")
            print(f"\n{complexity.explanation}")
        
        # ========================================
        # RESULTADOS FINALES
        # ========================================
        if verbose:
            print_separator("RESULTADOS FINALES", "=")
            print(f"\n🎯 Complejidad Computacional:")
            print(f"   • Peor caso (Big-O):     {complexity.big_o}")
            print(f"   • Mejor caso (Omega):    {complexity.omega}")
            print(f"   • Caso promedio (Theta): {complexity.theta}")
            print_separator("", "=")
        
        return {
            "ast": ast,
            "recursion_info": recursion_info,
            "complexity": complexity,
            "success": True
        }
    
    except SemanticError as e:
        print(f"\n❌ ERROR SEMÁNTICO:")
        print(f"   {e}")
        return {"success": False, "error": str(e), "error_type": "semantic"}
    
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "error_type": "unknown"}


def interactive_mode():
    """Modo interactivo para analizar múltiples archivos"""
    print_separator("MODO INTERACTIVO")
    print("\nIngresa la ruta del archivo a analizar (o 'exit' para salir):")
    
    while True:
        filepath = input("\n📂 Archivo: ").strip()
        
        if filepath.lower() in ('exit', 'quit', 'q'):
            print("\n👋 ¡Hasta luego!")
            break
        
        if not filepath:
            continue
        
        analyze_pseudocode(filepath, verbose=True, show_ast=False)


def batch_mode(directory="examples"):
    """Analiza todos los archivos .txt en un directorio"""
    print_separator("MODO BATCH")
    
    example_dir = Path(directory)
    if not example_dir.exists():
        print(f"❌ El directorio '{directory}' no existe")
        return
    
    txt_files = list(example_dir.glob("*.txt"))
    
    if not txt_files:
        print(f"❌ No se encontraron archivos .txt en '{directory}'")
        return
    
    print(f"\n📁 Analizando {len(txt_files)} archivo(s) en '{directory}'...\n")
    
    results = []
    for i, filepath in enumerate(txt_files, 1):
        print(f"\n{'='*80}")
        print(f"ARCHIVO {i}/{len(txt_files)}: {filepath.name}")
        print(f"{'='*80}")
        
        result = analyze_pseudocode(str(filepath), verbose=True, show_ast=False)
        results.append({
            "file": filepath.name,
            "result": result
        })
        
        print("\n")
    
    # Resumen final
    print_separator("RESUMEN DE ANÁLISIS BATCH")
    print(f"\nArchivos analizados: {len(results)}")
    successful = sum(1 for r in results if r["result"] and r["result"].get("success"))
    print(f"Exitosos: {successful}")
    print(f"Fallidos: {len(results) - successful}")
    
    print("\n📊 Resultados:")
    for r in results:
        status = "✓" if r["result"] and r["result"].get("success") else "✗"
        print(f"  {status} {r['file']}")
        if r["result"] and r["result"].get("success"):
            comp = r["result"]["complexity"]
            print(f"      → O({comp.big_o})")


def main():
    """Función principal con menú de opciones"""
    
    # Si se pasa un argumento, analizarlo directamente
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        show_ast = "--ast" in sys.argv
        analyze_pseudocode(filepath, verbose=True, show_ast=show_ast)
        return
    
    # Menú interactivo
    print_separator("ANALIZADOR DE COMPLEJIDAD COMPUTACIONAL")
    print("""
Selecciona una opción:

1. Analizar un archivo específico
2. Analizar todos los archivos en /examples
3. Modo interactivo
4. Salir

Uso desde línea de comandos:
    python main.py <archivo.txt>          # Analizar un archivo
    python main.py <archivo.txt> --ast    # Mostrar AST también
    """)
    
    while True:
        try:
            opcion = input("\nOpción: ").strip()
            
            if opcion == "1":
                filepath = input("Ruta del archivo: ").strip()
                show_ast = input("¿Mostrar AST? (s/n): ").strip().lower() == 's'
                analyze_pseudocode(filepath, verbose=True, show_ast=show_ast)
            
            elif opcion == "2":
                batch_mode("examples")
            
            elif opcion == "3":
                interactive_mode()
            
            elif opcion == "4":
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("❌ Opción inválida. Intenta de nuevo.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrumpido por el usuario. ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()