#!/usr/bin/env python3
"""
Script de prueba para el nuevo paquete de scraping.
"""

import logging
from datetime import datetime

from ..scraper import ScrapingService
from ..models import SearchRequest

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_scraping_package():
    """Prueba el nuevo paquete de scraping."""
    
    print("🧪 Probando nuevo paquete de scraping...")
    print("=" * 60)
    
    # Crear instancia del servicio
    scraping_service = ScrapingService()
    
    # Crear solicitud de búsqueda
    request = SearchRequest(
        fecha_inicio="1992-01-01",
        fecha_fin="2025-08-17",
        palabra="Marcela como agente oficiosa de su nieta Sara en contra de la Secretaría de Educación",
        extra="",
        pagina=0
    )
    
    print(f"📅 Fecha inicio: {request.fecha_inicio}")
    print(f"📅 Fecha fin: {request.fecha_fin}")
    print(f"🔍 Palabra de búsqueda: {request.palabra}")
    print(f"📄 Página: {request.pagina}")
    print("-" * 60)
    
    try:
        print("🚀 Ejecutando búsqueda...")
        
        # Realizar búsqueda
        response = await scraping_service.search_sentencias(request)
        
        print(f"✅ Búsqueda completada exitosamente!")
        print(f"📊 Total de resultados: {response.total_resultados}")
        print(f"📝 Nota: {response.nota}")
        
        # Mostrar resultados
        for i, resultado in enumerate(response.resultados, 1):
            print(f"\n🔍 Resultado {i}:")
            print(f"   📋 Tema: {resultado.tema}")
            print(f"   📄 Subtema: {resultado.subtema}")
            
            for j, providencia in enumerate(resultado.providencias, 1):
                print(f"   📜 Providencia {j}: {providencia.titulo}")
                print(f"      🌐 HTML: {providencia.url_html}")
                print(f"      📄 PDF: {providencia.url_pdf}")
        
        print("\n🎉 Prueba completada exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error durante la búsqueda: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sync_functions():
    """Prueba funciones síncronas del paquete."""
    
    print("\n🧪 Probando funciones síncronas...")
    print("=" * 60)
    
    try:
        from ..utils import build_search_url, extract_sentencia_number
        from ..config import ScrapingConfig
        
        # Probar construcción de URL
        url = build_search_url("1992-01-01", "2025-08-17", "test", "", 0)
        print(f"🔗 URL construida: {url}")
        
        # Probar extracción de número de sentencia
        texto = "Esta es la sentencia T-322/25 del año 2025"
        sentencia = extract_sentencia_number(texto)
        print(f"📜 Sentencia extraída: {sentencia}")
        
        # Probar configuración
        headers = ScrapingConfig.get_headers()
        print(f"⚙️ Headers configurados: {len(headers)} elementos")
        
        print("✅ Funciones síncronas funcionando correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en funciones síncronas: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Ejecuta todas las pruebas del paquete."""
    import asyncio
    
    print("🚀 INICIANDO PRUEBAS DEL PAQUETE DE SCRAPING")
    print("=" * 60)
    
    # Probar funciones síncronas
    sync_success = test_sync_functions()
    
    # Probar funciones asíncronas
    async_success = asyncio.run(test_scraping_package())
    
    print("\n" + "=" * 60)
    print("🏁 RESUMEN DE PRUEBAS")
    print("=" * 60)
    print(f"📋 Funciones síncronas: {'✅ EXITOSO' if sync_success else '❌ FALLÓ'}")
    print(f"🔄 Funciones asíncronas: {'✅ EXITOSO' if async_success else '❌ FALLÓ'}")
    
    if sync_success and async_success:
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("✨ El nuevo paquete de scraping está funcionando correctamente")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
    
    print("\n🎯 Prueba completada")
    
    return sync_success and async_success

if __name__ == "__main__":
    run_all_tests()
