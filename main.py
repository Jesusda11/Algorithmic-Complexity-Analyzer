"""
Analizador de Complejidad Computacional - VERSIÓN MEJORADA
Pipeline completo: Lexer → Parser → Detección Recursión → Análisis Complejidad → Clasificación Patrones
"""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Imports del proyecto
from lexer.lexer import Lexer
from parser.parser import Parser
from semantic.validator import validate_pseudocode, SemanticError
from analyzer.recursion import RecursionDetector
from analyzer.complexity import ComplexityAnalyzer
from analyzer.patterns import PatternClassifier, PatternType


# =============================================
# UTILIDADES DE PRESENTACIÓN
# =============================================

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


def print_header():
    """Imprime el encabezado del programa"""
    print_separator("ANALIZADOR DE COMPLEJIDAD COMPUTACIONAL")
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ANALIZADOR DE COMPLEJIDAD ALGORÍTMICA                     ║
║                                                                              ║
║  Características:                                                            ║
║    ✓ Análisis de complejidad O, Ω, Θ                                        ║
║    ✓ Detección de recursión (directa, indirecta, cola)                      ║
║    ✓ Resolución de relaciones de recurrencia (Master Theorem)               ║
║    ✓ Clasificación de patrones algorítmicos clásicos                        ║
║    ✓ Análisis de mejor, peor y caso promedio                                ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)


# =============================================
# PIPELINE DE ANÁLISIS PRINCIPAL
# =============================================

def analyze_pseudocode(filepath: str, verbose: bool = True, show_ast: bool = False, 
                      enable_patterns: bool = True) -> Dict:
    """
    Pipeline completo de análisis de pseudocódigo
    
    Args:
        filepath: Ruta al archivo de pseudocódigo
        verbose: Si True, muestra información detallada
        show_ast: Si True, muestra el AST completo
        enable_patterns: Si True, ejecuta clasificación de patrones
        
    Returns:
        dict con resultados del análisis
    """
    
    # ========================================
    # CARGAR PSEUDOCÓDIGO
    # ========================================
    if verbose:
        print_separator("ARCHIVO DE ENTRADA")
        print(f"\n📂 Ruta: {filepath}")
    
    code = read_file(filepath)
    
    if verbose:
        lines = code.count('\n') + 1
        print(f"📝 Pseudocódigo cargado:")
        print(f"   • Caracteres: {len(code)}")
        print(f"   • Líneas: {lines}")
        print("\n" + "-" * 80)
        # Mostrar primeras líneas
        preview_lines = code.split('\n')[:15]
        for i, line in enumerate(preview_lines, 1):
            print(f"{i:3d} | {line}")
        if len(code.split('\n')) > 15:
            print(f"    | ... y {len(code.split('\n')) - 15} líneas más")
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
            print(f"✓ Tokenización completada")
            print(f"   • Total de tokens: {len(tokens)}")
            
            # Estadísticas de tokens
            token_types = {}
            for tok in tokens:
                token_types[tok.type] = token_types.get(tok.type, 0) + 1
            
            print(f"   • Tipos únicos: {len(token_types)}")
            print("\n📊 Primeros 10 tokens:")
            for i, tok in enumerate(tokens[:10], 1):
                print(f"   {i:2d}. {tok.type:<15} | {str(tok.value):<20} | línea {tok.line}")
            
            if len(tokens) > 10:
                print(f"   ... y {len(tokens) - 10} tokens más")
        
        # ========================================
        # FASE 2: ANÁLISIS SINTÁCTICO
        # ========================================
        if verbose:
            print_phase(2, "Análisis Sintáctico (Construcción del AST)")
        
        parser = Parser(tokens)
        ast = parser.parse()
        
        if verbose:
            print(f"✓ AST generado exitosamente")
            print(f"\n📊 Estructura del programa:")
            print(f"   • Clases definidas: {len(ast.get('classes', []))}")
            print(f"   • Grafos definidos: {len(ast.get('graphs', []))}")
            print(f"   • Procedimientos: {len(ast.get('procedures', []))}")
            print(f"   • Statements principales: {len(ast.get('body', []))}")
            
            # Listar procedimientos con detalles
            if ast.get('procedures'):
                print("\n   Procedimientos encontrados:")
                for proc in ast['procedures']:
                    params = len(proc.get('params', []))
                    param_names = [p.get('name', '?') for p in proc.get('params', [])]
                    print(f"      • {proc['name']}({', '.join(param_names)})")
            
            # Listar clases
            if ast.get('classes'):
                print("\n   Clases definidas:")
                for cls in ast['classes']:
                    attrs = len(cls.get('attributes', []))
                    print(f"      • {cls['name']} ({attrs} atributos)")
            
            # Listar grafos
            if ast.get('graphs'):
                print("\n   Grafos definidos:")
                for graph in ast['graphs']:
                    print(f"      • {graph['name']} (dirigido: {graph.get('dirigido', False)})")
        
        if show_ast:
            print("\n" + "="*80)
            print("📊 AST COMPLETO:")
            print("="*80)
            print(json.dumps(ast, indent=2, ensure_ascii=False))
            print("="*80)
        
        # ========================================
        # FASE 3: VALIDACIÓN SEMÁNTICA (Opcional)
        # ========================================
        # Descomentado si tienes validator implementado
        # if verbose:
        #     print_phase(3, "Validación Semántica")
        # try:
        #     validate_pseudocode(ast)
        #     if verbose:
        #         print("✓ Validación semántica completada sin errores")
        # except SemanticError as e:
        #     print(f"⚠️  Advertencia semántica: {e}")
        
        # ========================================
        # FASE 4: DETECCIÓN DE RECURSIÓN
        # ========================================
        if verbose:
            print_phase(4, "Análisis de Recursión")
        
        detector = RecursionDetector(ast)
        recursion_info = detector.analyze()
        
        if verbose:
            if ast.get('procedures'):
                recursive_procs = [name for name, info in recursion_info.items() if info.is_recursive]
                
                if recursive_procs:
                    print(f"✓ Recursión detectada en {len(recursive_procs)} procedimiento(s):\n")
                    
                    for proc_name in recursive_procs:
                        info = recursion_info[proc_name]
                        print(f"   📌 {proc_name}:")
                        print(f"      • Tipo: {info.recursion_type}")
                        print(f"      • Patrón de profundidad: {info.depth_pattern}")
                        print(f"      • Llamadas recursivas: {info.call_count}")
                        print(f"      • Subproblema: {info.subproblem}")
                        print(f"      • Trabajo de combinación: {'Sí' if info.has_combining_work else 'No'}")
                        print()
                else:
                    print("✓ No se detectó recursión en ningún procedimiento")
            else:
                print("   ℹ️  No hay procedimientos definidos para analizar")
        
        # ========================================
        # FASE 5: ANÁLISIS DE COMPLEJIDAD
        # ========================================
        if verbose:
            print_phase(5, "Análisis de Complejidad Computacional")
        
        analyzer = ComplexityAnalyzer(ast, recursion_info)
        complexity = analyzer.analyze()
        
        if verbose:
            print("✓ Análisis de complejidad completado")
            
            # Mostrar si hay análisis por procedimiento
            if hasattr(complexity, 'per_procedure_analysis') and complexity.per_procedure_analysis:
                print(f"\n   Procedimientos analizados: {len(complexity.per_procedure_analysis)}")
                for proc_name in complexity.per_procedure_analysis.keys():
                    print(f"      • {proc_name}")

        # ========================================
        # FASE 6: CLASIFICACIÓN DE PATRONES
        # ========================================
        if enable_patterns and verbose:
            print_phase(6, "Clasificación de Patrones Algorítmicos")
            
            classifier = PatternClassifier()
            patterns_found = False
            unknown_patterns = []
            
            if hasattr(complexity, 'per_procedure_analysis') and complexity.per_procedure_analysis:
                for proc_name, data in complexity.per_procedure_analysis.items():
                    rec_info = data["recursion_info"]
                    relation = data.get("relation")
                    solution = data["solution"]
                    
                    classification = classifier.classify(
                        func_name=proc_name,
                        recursion_info=rec_info,
                        recurrence_solution=solution,
                        recurrence_relation=relation
                    )
                    
                    if classification.pattern != PatternType.UNKNOWN:
                        patterns_found = True
                        classifier.print_classification(classification, proc_name)
                    else:
                        unknown_patterns.append((proc_name, rec_info, solution))
                
                # Mostrar patrones no reconocidos al final
                if unknown_patterns:
                    print("\n" + "─"*80)
                    print("📋 Procedimientos sin patrón clásico reconocido:")
                    print("─"*80)
                    for proc_name, rec_info, solution in unknown_patterns:
                        print(f"\n   • {proc_name}:")
                        if rec_info.is_recursive:
                            print(f"      Tipo: {rec_info.recursion_type}")
                            print(f"      Patrón: {rec_info.depth_pattern}")
                            print(f"      Complejidad estimada: {solution.complexity}")
                        else:
                            print(f"      Algoritmo iterativo")
                
                # Mensaje final
                if patterns_found:
                    print("\n" + "="*80)
                    print("✅ Se detectaron patrones algorítmicos clásicos")
                    print("="*80)
            else:
                print("\n   ℹ️  No hay procedimientos recursivos para clasificar")

        # ========================================
        # RESULTADOS FINALES
        # ========================================
        if verbose:
            print_separator("📊 RESULTADOS FINALES", "═")
            print(f"\n🎯 Complejidad Computacional del Programa:")
            print(f"   ┌─────────────────────────────────────────────")
            print(f"   │ Peor caso (Big-O):      {complexity.big_o}")
            print(f"   │ Mejor caso (Omega):     {complexity.omega}")
            print(f"   │ Caso promedio (Theta):  {complexity.theta}")
            print(f"   └─────────────────────────────────────────────")
            
            if complexity.recurrence_info:
                print(f"\n🔄 Relaciones de Recurrencia Resueltas:")
                for proc_name, sol in complexity.recurrence_info.items():
                    print(f"   • {proc_name}:")
                    print(f"      Relación: {sol['relation']}")
                    print(f"      Solución: {sol['solution']}")
                    print(f"      Método: {sol['method']}")
            
            print_separator("", "═")
        
        return {
            "ast": ast,
            "tokens": tokens,
            "recursion_info": recursion_info,
            "complexity": complexity,
            "success": True,
            "filepath": filepath
        }
    
    except SemanticError as e:
        print(f"\n❌ ERROR SEMÁNTICO:")
        print(f"   {e}")
        return {"success": False, "error": str(e), "error_type": "semantic"}
    
    except Exception as e:
        print(f"\n❌ ERROR INESPERADO:")
        print(f"   Tipo: {type(e).__name__}")
        print(f"   Mensaje: {e}")
        
        if verbose:
            print("\n🔍 Traza completa del error:")
            import traceback
            traceback.print_exc()
        
        return {"success": False, "error": str(e), "error_type": "unknown"}


# =============================================
# MODOS DE OPERACIÓN
# =============================================

def interactive_mode():
    """Modo interactivo para analizar múltiples archivos"""
    print_separator("MODO INTERACTIVO", "═")
    print("\n💡 Comandos disponibles:")
    print("   • Ruta de archivo: analiza el archivo")
    print("   • 'exit' / 'quit' / 'q': salir")
    print("   • 'help': mostrar ayuda")
    
    while True:
        try:
            filepath = input("\n📂 Archivo: ").strip()
            
            if filepath.lower() in ('exit', 'quit', 'q'):
                print("\n👋 ¡Hasta luego!")
                break
            
            if filepath.lower() == 'help':
                print("\n📖 Ayuda:")
                print("   Ingresa la ruta de un archivo .txt con pseudocódigo")
                print("   El analizador procesará el archivo y mostrará:")
                print("     - Complejidad temporal (O, Ω, Θ)")
                print("     - Patrones algorítmicos detectados")
                print("     - Relaciones de recurrencia (si hay recursión)")
                continue
            
            if not filepath:
                continue
            
            analyze_pseudocode(filepath, verbose=True, show_ast=False)
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrumpido. ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def batch_mode(directory="examples"):
    """Analiza todos los archivos .txt en un directorio"""
    print_separator("MODO BATCH", "═")
    
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
        print(f"\n{'═'*80}")
        print(f"ARCHIVO {i}/{len(txt_files)}: {filepath.name}")
        print(f"{'═'*80}")
        
        result = analyze_pseudocode(str(filepath), verbose=True, show_ast=False)
        results.append({
            "file": filepath.name,
            "result": result
        })
        
        input("\n⏸️  Presiona ENTER para continuar al siguiente archivo...")
    
    # Resumen final
    print_separator("📊 RESUMEN DEL ANÁLISIS BATCH", "═")
    
    successful = sum(1 for r in results if r["result"] and r["result"].get("success"))
    failed = len(results) - successful
    
    print(f"\n📈 Estadísticas:")
    print(f"   • Archivos analizados: {len(results)}")
    print(f"   • Exitosos: {successful} ({successful/len(results)*100:.1f}%)")
    print(f"   • Fallidos: {failed}")
    
    print("\n📋 Resultados detallados:")
    print("─"*80)
    
    for r in results:
        status = "✅" if r["result"] and r["result"].get("success") else "❌"
        filename = r['file']
        
        if r["result"] and r["result"].get("success"):
            comp = r["result"]["complexity"]
            print(f"{status} {filename:<40} → O({comp.big_o})")
        else:
            error = r["result"].get("error", "Error desconocido")
            print(f"{status} {filename:<40} → Error: {error}")
    
    print("─"*80)


def compare_mode():
    """Modo de comparación entre algoritmos"""
    print_separator("MODO COMPARACIÓN", "═")
    print("\n🔬 Compara múltiples algoritmos")
    
    algorithms = []
    
    print("\nIngresa rutas de archivos (vacío para terminar):")
    while True:
        filepath = input(f"   Algoritmo {len(algorithms)+1}: ").strip()
        if not filepath:
            break
        
        if Path(filepath).exists():
            algorithms.append(filepath)
            print(f"      ✓ Agregado")
        else:
            print(f"      ❌ No existe")
    
    if len(algorithms) < 2:
        print("\n⚠️  Se necesitan al menos 2 algoritmos para comparar")
        return
    
    print(f"\n📊 Analizando {len(algorithms)} algoritmos...\n")
    
    results = []
    for filepath in algorithms:
        print(f"Analizando: {Path(filepath).name}...")
        result = analyze_pseudocode(filepath, verbose=False, show_ast=False)
        results.append({
            "name": Path(filepath).stem,
            "result": result
        })
    
    # Tabla comparativa
    print("\n" + "═"*80)
    print("TABLA COMPARATIVA")
    print("═"*80)
    print(f"{'Algoritmo':<30} | {'Big-O':<15} | {'Omega':<15} | {'Theta':<15}")
    print("─"*80)
    
    for r in results:
        if r["result"].get("success"):
            comp = r["result"]["complexity"]
            print(f"{r['name']:<30} | O({comp.big_o:<13}) | Ω({comp.omega:<13}) | Θ({comp.theta:<13})")
        else:
            print(f"{r['name']:<30} | {'ERROR':<15} | {'ERROR':<15} | {'ERROR':<15}")
    
    print("═"*80)


def test_mode():
    """Ejecuta tests del sistema"""
    print_separator("MODO TEST", "═")
    print("\n🧪 Ejecutando tests del sistema...\n")
    
    # Test RecurrenceSolver
    print("1️⃣  Tests de RecurrenceSolver:")
    print("─"*80)
    try:
        from analyzer.recurrence import test_binary_search_detection
        test_binary_search_detection()
        print("\n✅ RecurrenceSolver: OK")
    except Exception as e:
        print(f"\n❌ RecurrenceSolver: FAIL - {e}")
    
    # Test CaseAnalyzer
    print("\n2️⃣  Tests de CaseAnalyzer:")
    print("─"*80)
    try:
        from analyzer.case_analyzer import test_search_with_early_exit
        test_search_with_early_exit()
        print("\n✅ CaseAnalyzer: OK")
    except Exception as e:
        print(f"\n❌ CaseAnalyzer: FAIL - {e}")
    
    # Test RecursionDetector
    print("\n3️⃣  Tests de RecursionDetector:")
    print("─"*80)
    try:
        from analyzer.recursion import test_mergesort_detection
        test_mergesort_detection()
        print("\n✅ RecursionDetector: OK")
    except Exception as e:
        print(f"\n❌ RecursionDetector: FAIL - {e}")
    
    print("\n" + "═"*80)
    print("✅ Suite de tests completada")
    print("═"*80)


# =============================================
# FUNCIÓN PRINCIPAL
# =============================================

def main():
    """Función principal con menú de opciones"""
    
    # Si se pasa un argumento, analizarlo directamente
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        show_ast = "--ast" in sys.argv
        no_patterns = "--no-patterns" in sys.argv
        
        analyze_pseudocode(filepath, verbose=True, show_ast=show_ast, 
                         enable_patterns=not no_patterns)
        return
    
    # Menú interactivo
    print_header()
    
    menu = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                              MENÚ PRINCIPAL                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  1. Analizar un archivo específico                                           ║
║  2. Analizar todos los archivos en /examples (modo batch)                    ║
║  3. Modo interactivo (analizar múltiples archivos)                           ║
║  4. Modo comparación (comparar algoritmos)                                   ║
║  5. Ejecutar suite de tests                                                  ║
║  6. Salir                                                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Uso desde línea de comandos:                                                ║
║    python main.py <archivo.txt>              # Analizar un archivo           ║
║    python main.py <archivo.txt> --ast        # Mostrar AST también           ║
║    python main.py <archivo.txt> --no-patterns # Sin clasificación patrones  ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    
    print(menu)
    
    while True:
        try:
            opcion = input("Selecciona una opción [1-6]: ").strip()
            
            if opcion == "1":
                filepath = input("\n📂 Ruta del archivo: ").strip()
                show_ast = input("¿Mostrar AST completo? (s/n) [n]: ").strip().lower() == 's'
                analyze_pseudocode(filepath, verbose=True, show_ast=show_ast)
            
            elif opcion == "2":
                batch_mode("examples")
            
            elif opcion == "3":
                interactive_mode()
            
            elif opcion == "4":
                compare_mode()
            
            elif opcion == "5":
                test_mode()
            
            elif opcion == "6":
                print("\n" + "═"*80)
                print("👋 ¡Gracias por usar el Analizador de Complejidad!")
                print("═"*80)
                break
            
            else:
                print("❌ Opción inválida. Selecciona un número entre 1 y 6.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrumpido por el usuario. ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()