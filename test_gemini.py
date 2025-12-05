"""
Script para probar la integración con Gemini
"""

import asyncio
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.services.llm_service import llm_client
from app.services.llm_assistant_service import llm_assistant


async def test_connection():
    """Prueba básica de conexión"""
    print("=" * 70)
    print("🧪 TEST 1: CONEXIÓN CON GEMINI")
    print("=" * 70)
    
    print(f"\n📋 Configuración:")
    print(f"   Proveedor: {settings.LLM_PROVIDER}")
    print(f"   Modelo: {settings.get_active_model()}")
    print(f"   API Key: {settings.GEMINI_API_KEY[:20]}..." if settings.GEMINI_API_KEY else "   API Key: ❌ NO CONFIGURADA")
    
    if not llm_client.is_available():
        print("\n❌ Cliente no disponible. Verifica tu API key.")
        return False
    
    print("\n🔄 Enviando prompt de prueba...")
    
    try:
        response = await llm_client.generate(
            prompt="Responde solo con 'OK' si me recibes correctamente.",
            system_prompt="Eres un asistente que responde brevemente.",
            temperature=0.0
        )
        
        print(f"✅ Respuesta recibida: '{response[:100]}'")
        return True
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def test_translation():
    """Prueba de traducción de lenguaje natural"""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: TRADUCCIÓN A PSEUDOCÓDIGO")
    print("=" * 70)
    
    # Primero habilitar la feature
    settings.ENABLE_LLM_TRANSLATION = True
    
    natural_language = """
    Crea un algoritmo de búsqueda binaria que busque un elemento x 
    en un arreglo ordenado A. El algoritmo debe dividir el arreglo 
    por la mitad recursivamente hasta encontrar el elemento o determinar 
    que no existe.
    """
    
    print(f"\n📝 Input (lenguaje natural):")
    print(f"   {natural_language.strip()}")
    
    print("\n🔄 Traduciendo...")
    
    try:
        pseudocode = await llm_assistant.translate_to_pseudocode(natural_language)
        
        print("\n✅ Pseudocódigo generado:")
        print("-" * 70)
        print(pseudocode)
        print("-" * 70)
        return True
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def test_verification():
    """Prueba de verificación de análisis"""
    print("\n" + "=" * 70)
    print("🧪 TEST 3: VERIFICACIÓN DE ANÁLISIS")
    print("=" * 70)
    
    # Habilitar feature
    settings.ENABLE_LLM_VERIFICATION = True
    
    pseudocode = """
    procedure BusquedaLineal(A, x, n)
    begin
        for i 🡨 1 to n do
        begin
            if (A[i] = x) then
            begin
                return i
            end
        end
        return -1
    end
    """
    
    our_analysis = {
        "big_o": "n",
        "omega": "1",
        "theta": "n"
    }
    
    steps = [
        "Analizando ciclo FOR: 1 to n",
        "Cuerpo del ciclo: O(1)",
        "Total: O(n)"
    ]
    
    print(f"\n📝 Pseudocódigo:")
    print(pseudocode)
    print(f"\n📊 Nuestro análisis: O({our_analysis['big_o']}), Ω({our_analysis['omega']}), Θ({our_analysis['theta']})")
    
    print("\n🔄 Verificando con Gemini...")
    
    try:
        verification = await llm_assistant.verify_analysis(
            pseudocode, our_analysis, steps
        )
        
        print("\n✅ Verificación completada:")
        print(f"   Correcto: {verification.get('is_correct', 'N/A')}")
        print(f"   Confianza: {verification.get('confidence', 0):.0%}")
        
        if verification.get('issues'):
            print(f"   Issues: {verification['issues']}")
        
        if verification.get('suggestions'):
            print(f"   Sugerencias: {verification['suggestions']}")
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


async def test_pattern_classification():
    """Prueba de clasificación de patrones"""
    print("\n" + "=" * 70)
    print("🧪 TEST 4: CLASIFICACIÓN DE PATRONES")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_connection())
    asyncio.run(test_translation())
    asyncio.run(test_verification())
    # asyncio.run(test_pattern_classification())
