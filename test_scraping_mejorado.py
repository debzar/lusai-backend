#!/usr/bin/env python3
"""
Script de prueba para el servicio de scraping mejorado de la Corte Constitucional.
"""

import sys
import os
import logging
from datetime import datetime

# Agregar el directorio app al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.scraping_service import buscar_sentencias

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_scraping():
    """Prueba el servicio de scraping con diferentes parámetros."""
    
    print("🧪 Probando servicio de scraping mejorado...")
    print("=" * 60)
    
    # Parámetros de prueba
    fecha_inicio = "1992-01-01"
    fecha_fin = "2025-08-17"
    palabra_busqueda = "Marcela como agente oficiosa de su nieta Sara en contra de la Secretaría de Educación"
    
    print(f"📅 Fecha inicio: {fecha_inicio}")
    print(f"📅 Fecha fin: {fecha_fin}")
    print(f"🔍 Palabra de búsqueda: {palabra_busqueda}")
    print(f"📄 Página: 0")
    print("-" * 60)
    
    try:
        # Ejecutar búsqueda
        print("🚀 Ejecutando búsqueda...")
        inicio = datetime.now()
        
        resultados = buscar_sentencias(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            palabra=palabra_busqueda,
            extra="",
            pagina=0
        )
        
        fin = datetime.now()
        tiempo_ejecucion = (fin - inicio).total_seconds()
        
        print(f"✅ Búsqueda completada en {tiempo_ejecucion:.2f} segundos")
        print(f"📊 Total de resultados encontrados: {len(resultados)}")
        print("-" * 60)
        
        # Mostrar resultados
        if resultados:
            print("📋 RESULTADOS ENCONTRADOS:")
            print("-" * 60)
            
            for i, resultado in enumerate(resultados, 1):
                print(f"\n🔍 Resultado {i}:")
                print(f"   📝 Tema: {resultado.get('tema', 'N/A')}")
                print(f"   📄 Subtema: {resultado.get('subtema', 'N/A')}")
                
                if 'providencias' in resultado and resultado['providencias']:
                    for j, providencia in enumerate(resultado['providencias'], 1):
                        print(f"   📜 Providencia {j}:")
                        print(f"      🏷️  Título: {providencia.get('titulo', 'N/A')}")
                        print(f"      🌐 URL HTML: {providencia.get('url_html', 'N/A')}")
                        print(f"      📄 URL PDF: {providencia.get('url_pdf', 'N/A')}")
                else:
                    print("   ⚠️  No se encontraron providencias")
                    
                print("   " + "-" * 40)
        else:
            print("❌ No se encontraron resultados")
            
    except Exception as e:
        print(f"❌ Error durante la búsqueda: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 Prueba completada")

def test_scraping_simple():
    """Prueba con una búsqueda más simple."""
    
    print("\n🧪 Probando búsqueda simple...")
    print("=" * 60)
    
    fecha_inicio = "2020-01-01"
    fecha_fin = "2025-08-17"
    palabra_busqueda = "agente oficioso"
    
    print(f"🔍 Búsqueda simple: {palabra_busqueda}")
    
    try:
        resultados = buscar_sentencias(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            palabra=palabra_busqueda,
            extra="",
            pagina=0
        )
        
        print(f"📊 Resultados encontrados: {len(resultados)}")
        
        if resultados:
            print("📋 Primer resultado:")
            primer_resultado = resultados[0]
            print(f"   📝 Tema: {primer_resultado.get('tema', 'N/A')}")
            if 'providencias' in primer_resultado and primer_resultado['providencias']:
                print(f"   📜 Primera providencia: {primer_resultado['providencias'][0].get('titulo', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Error en búsqueda simple: {e}")

if __name__ == "__main__":
    print("🚀 INICIANDO PRUEBAS DE SCRAPING")
    print("=" * 60)
    
    # Prueba principal
    test_scraping()
    
    # Prueba simple
    test_scraping_simple()
    
    print("\n🎉 Todas las pruebas completadas")
