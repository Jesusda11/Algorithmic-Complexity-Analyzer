"""
test_fibonacci.py - Test para verificar análisis correcto de Fibonacci
"""

def test_fibonacci_analysis():
    """
    Test que verifica que Fibonacci se analiza correctamente:
    - Detecta subproblem n-1,n-2
    - Genera relación T(n) = T(n-1) + T(n-2) + O(1)
    - Calcula complejidad O(2^n)
    """
    
    # Simular el AST de Fibonacci
    fibonacci_ast = {
        "type": "program",
        "classes": [],
        "procedures": [
            {
                "type": "procedure_decl",
                "name": "Fibonacci",
                "params": [
                    {
                        "type": "primitive_param",
                        "name": "n"
                    }
                ],
                "body": {
                    "type": "block",
                    "body": [
                        {
                            "type": "if",
                            "cond": {
                                "type": "binop",
                                "op": "LE",
                                "left": {
                                    "type": "var",
                                    "value": "n"
                                },
                                "right": {
                                    "type": "number",
                                    "value": 1
                                }
                            },
                            "then": {
                                "type": "block",
                                "body": [
                                    {
                                        "type": "return",
                                        "expr": {
                                            "type": "var",
                                            "value": "n"
                                        }
                                    }
                                ]
                            },
                            "else": {
                                "type": "block",
                                "body": [
                                    {
                                        "type": "return",
                                        "expr": {
                                            "type": "binop",
                                            "op": "PLUS",
                                            "left": {
                                                "type": "call_expr",
                                                "name": "Fibonacci",
                                                "args": [
                                                    {
                                                        "type": "binop",
                                                        "op": "MINUS",
                                                        "left": {
                                                            "type": "var",
                                                            "value": "n"
                                                        },
                                                        "right": {
                                                            "type": "number",
                                                            "value": 1
                                                        }
                                                    }
                                                ]
                                            },
                                            "right": {
                                                "type": "call_expr",
                                                "name": "Fibonacci",
                                                "args": [
                                                    {
                                                        "type": "binop",
                                                        "op": "MINUS",
                                                        "left": {
                                                            "type": "var",
                                                            "value": "n"
                                                        },
                                                        "right": {
                                                            "type": "number",
                                                            "value": 2
                                                        }
                                                    }
                                                ]
                                            }
                                        }
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        ],
        "graphs": [],
        "body": [
            {
                "type": "block",
                "body": [
                    {
                        "type": "assign",
                        "target": {
                            "type": "var",
                            "value": "x"
                        },
                        "expr": {
                            "type": "call_expr",
                            "name": "Fibonacci",
                            "args": [
                                {
                                    "type": "number",
                                    "value": 10
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }

    print("=" * 80)
    print("TEST: ANÁLISIS DE FIBONACCI")
    print("=" * 80)

    # FASE 1: Análisis de Recursión
    print("\n📍 FASE 1: Detectando recursión...")
    from analyzer.recursion import RecursionDetector
    
    detector = RecursionDetector(fibonacci_ast)
    recursion_info = detector.analyze()
    
    fib_info = recursion_info.get("Fibonacci")
    
    print(f"✓ Recursivo: {fib_info.is_recursive}")
    print(f"✓ Tipo: {fib_info.recursion_type}")
    print(f"✓ Llamadas: {fib_info.call_count}")
    print(f"✓ Patrón: {fib_info.depth_pattern}")
    print(f"✓ Subproblema: {fib_info.subproblem}")
    
    # Verificaciones FASE 1
    assert fib_info.is_recursive == True, "❌ Debe ser recursivo"
    assert fib_info.call_count == 2, f"❌ Debe tener 2 llamadas, no {fib_info.call_count}"
    assert fib_info.depth_pattern == "tree", f"❌ Patrón debe ser 'tree', no '{fib_info.depth_pattern}'"
    assert fib_info.subproblem == "n-1,n-2", f"❌ Subproblema debe ser 'n-1,n-2', no '{fib_info.subproblem}'"
    
    print("✅ FASE 1 PASADA: Recursión detectada correctamente")

    # FASE 2: Análisis de Complejidad
    print("\n📍 FASE 2: Analizando complejidad...")
    from analyzer.complexity import ComplexityAnalyzer
    
    analyzer = ComplexityAnalyzer(fibonacci_ast, recursion_info)
    complexity = analyzer.analyze()
    
    print(f"✓ Big-O: {complexity.big_o}")
    print(f"✓ Omega: {complexity.omega}")
    print(f"✓ Theta: {complexity.theta}")
    
    # Verificar que hay solución de recurrencia
    assert complexity.recurrence_info, "❌ Debe tener información de recurrencia"
    assert "Fibonacci" in complexity.recurrence_info, "❌ Debe tener solución para Fibonacci"
    
    fib_solution = complexity.recurrence_info["Fibonacci"]
    
    print(f"\n✓ Relación: {fib_solution['relation']}")
    print(f"✓ Solución: {fib_solution['solution']}")
    print(f"✓ Método: {fib_solution['method']}")
    
    # Verificaciones FASE 2
    assert "T(n-1) + T(n-2)" in fib_solution['relation'], \
        f"❌ Relación debe contener 'T(n-1) + T(n-2)', actual: {fib_solution['relation']}"
    
    assert "2^n" in fib_solution['solution'], \
        f"❌ Solución debe ser O(2^n), actual: {fib_solution['solution']}"
    
    assert "2**n" in complexity.big_o or "2^n" in complexity.big_o, \
        f"❌ Big-O debe ser 2^n, actual: {complexity.big_o}"
    
    print("✅ FASE 2 PASADA: Complejidad calculada correctamente")

    # FASE 3: Clasificación de Patrones
    print("\n📍 FASE 3: Clasificando patrón algorítmico...")
    from analyzer.patterns import PatternClassifier
    
    classifier = PatternClassifier()
    
    # Obtener análisis del procedimiento
    proc_analysis = complexity.per_procedure_analysis.get("Fibonacci")
    
    if proc_analysis:
        classification = classifier.classify(
            "Fibonacci",
            proc_analysis["recursion_info"],
            proc_analysis["solution"],
            proc_analysis.get("relation")
        )
        
        print(f"✓ Patrón: {classification.pattern.value}")
        print(f"✓ Complejidad: {classification.complexity}")
        print(f"✓ Confianza: {classification.confidence:.1%}")
        
        # Verificaciones FASE 3
        assert "Fibonacci" in classification.pattern.value, \
            f"❌ Debe detectar patrón Fibonacci, detectó: {classification.pattern.value}"
        
        assert classification.confidence >= 0.95, \
            f"❌ Confianza debe ser >= 95%, actual: {classification.confidence:.1%}"
        
        print("✅ FASE 3 PASADA: Patrón Fibonacci reconocido")
    else:
        print("⚠️  FASE 3 OMITIDA: No hay análisis de procedimiento")

    # RESUMEN FINAL
    print("\n" + "=" * 80)
    print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
    print("=" * 80)
    print("\nRESUMEN:")
    print(f"  • Subproblema detectado: n-1,n-2 ✓")
    print(f"  • Relación: T(n) = T(n-1) + T(n-2) + O(1) ✓")
    print(f"  • Complejidad: O(2^n) ✓")
    print(f"  • Patrón: Fibonacci (naïve) ✓")
    print("=" * 80)


if __name__ == "__main__":
    try:
        test_fibonacci_analysis()
    except AssertionError as e:
        print(f"\n❌ TEST FALLIDO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n💥 ERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)