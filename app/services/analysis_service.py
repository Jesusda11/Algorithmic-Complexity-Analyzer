# app/services/analysis_service.py
"""
Servicio principal de análisis - Orquesta todo el pipeline
"""
from typing import Dict, Optional
import time

from lexer.lexer import Lexer
from parser.parser import Parser
from analyzer.recursion import RecursionDetector
from analyzer.complexity import ComplexityAnalyzer
from analyzer.patterns import PatternClassifier

from app.models.response_models import (
    AnalysisResponse, ComplexityResponse, RecursionInfoResponse,
    ProcedureAnalysisResponse, PatternClassificationResponse,
    RecurrenceSolutionResponse, TokenInfo
)
from app.utils.exceptions import LexerError, ParserError, AnalysisError


class AnalysisService:
    """Servicio de análisis de complejidad"""
    
    def __init__(self):
        self.pattern_classifier = PatternClassifier()
    
    def analyze(
        self, 
        code: str,
        include_ast: bool = False,
        include_tokens: bool = False,
        enable_patterns: bool = True
    ) -> AnalysisResponse:
        """Analiza un pseudocódigo y retorna la complejidad computacional"""
        
        try:
            # 1. ANÁLISIS LÉXICO
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            
            # 2. ANÁLISIS SINTÁCTICO
            parser = Parser(tokens)
            ast = parser.parse()
            
            # 3. DETECCIÓN DE RECURSIÓN
            detector = RecursionDetector(ast)
            recursion_info = detector.analyze()
            
            # 4. ANÁLISIS DE COMPLEJIDAD
            analyzer = ComplexityAnalyzer(ast, recursion_info)
            complexity = analyzer.analyze()
            
            # 5. CONSTRUIR RESPUESTA
            complexity_response = ComplexityResponse(
                big_o=str(complexity.big_o),
                omega=str(complexity.omega),
                theta=str(complexity.theta),
                explanation=complexity.explanation,
                steps=complexity.steps
            )
            
            # Análisis por procedimiento
            procedures_response = None
            if hasattr(complexity, 'per_procedure_analysis') and complexity.per_procedure_analysis:
                procedures_response = self._build_procedures_response(
                    complexity.per_procedure_analysis,
                    enable_patterns
                )
            
            # Tokens (opcional)
            tokens_response = None
            if include_tokens:
                tokens_response = [
                    TokenInfo(
                        type=str(tok.type),
                        value=str(tok.value),
                        line=tok.line,
                        column=tok.col
                    )
                    for tok in tokens[:100]
                ]
            
            # AST (opcional)
            ast_response = ast if include_ast else None
            
            # Metadata
            metadata = {
                "lines_of_code": code.count('\n') + 1,
                "num_tokens": len(tokens),
                "num_procedures": len(ast.get('procedures', [])),
                "num_classes": len(ast.get('classes', [])),
                "has_recursion": any(info.is_recursive for info in recursion_info.values()),
                "analysis_timestamp": time.time()
            }
            
            return AnalysisResponse(
                success=True,
                complexity=complexity_response,
                procedures=procedures_response,
                tokens=tokens_response,
                ast=ast_response,
                metadata=metadata
            )
            
        except Exception as e:
            import traceback
            traceback.print_exc()  # ← ESTO MOSTRARÁ EL ERROR EN CONSOLA
            raise AnalysisError(
                message=str(e),
                details={"exception_type": type(e).__name__}
            )
    
    def _build_procedures_response(
        self, 
        per_procedure_analysis: Dict,
        enable_patterns: bool
    ) -> Dict[str, ProcedureAnalysisResponse]:
        """Construye la respuesta de análisis por procedimiento"""
        
        procedures = {}
        
        for proc_name, data in per_procedure_analysis.items():
            rec_info = data["recursion_info"]
            solution = data["solution"]
            relation = data.get("relation")
            
            # ========================================
            # FIX: Validar atributos antes de usar
            # ========================================
            
            # Recursión info
            recursion_response = RecursionInfoResponse(
                is_recursive=getattr(rec_info, 'is_recursive', False),
                recursion_type=getattr(rec_info, 'recursion_type', 'none'),
                call_count=getattr(rec_info, 'call_count', 0),
                depth_pattern=getattr(rec_info, 'depth_pattern', 'unknown'),
                subproblem=getattr(rec_info, 'subproblem', 'unknown'),
                has_combining_work=getattr(rec_info, 'has_combining_work', False)
            )
            
            # Recurrence solution (si existe)
            recurrence_response = None
            if relation:
                recurrence_response = RecurrenceSolutionResponse(
                    relation=str(relation),
                    solution=getattr(solution, 'complexity', 'O(?)'),
                    method=getattr(solution, 'method', 'Unknown'),
                    explanation=getattr(solution, 'explanation', 'No explanation available')
                )
            
            # Pattern classification (si está habilitado)
            pattern_response = None
            if enable_patterns:
                try:
                    classification = self.pattern_classifier.classify(
                        func_name=proc_name,
                        recursion_info=rec_info,
                        recurrence_solution=solution,
                        recurrence_relation=relation
                    )
                    
                    pattern_response = PatternClassificationResponse(
                        pattern=classification.pattern.value,
                        complexity=classification.complexity,
                        confidence=classification.confidence,
                        explanation=classification.explanation,
                        characteristics=getattr(classification, 'characteristics', None)
                    )
                except Exception as e:
                    print(f"⚠️ Error clasificando patrón para {proc_name}: {e}")
            
            # Construir respuesta del procedimiento
            procedures[proc_name] = ProcedureAnalysisResponse(
                name=proc_name,
                recursion_info=recursion_response,
                recurrence_solution=recurrence_response,
                pattern=pattern_response,
                complexity=getattr(solution, 'complexity', 'O(?)')
            )
        
        return procedures