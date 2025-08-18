#!/usr/bin/env python3
"""
Test específico para probar la URL de búsqueda de la Corte Constitucional.
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse
from ..config import ScrapingConfig

def test_specific_scraping():
    """Prueba la URL específica de búsqueda."""
    
    print("🧪 Probando URL específica de búsqueda...")
    print("=" * 60)
    
    # Probando la URL específica que proporcionaste
    texto_busqueda = "Marcela como agente oficiosa de su nieta Sara en contra de la Secretaría de Educación"
    
    # Diferentes formas de codificar
    url_normal = f"https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia/texto/1992-01-01/2025-08-17/{urllib.parse.quote(texto_busqueda, safe='')}/0/0"
    url_plus = f"https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia/texto/1992-01-01/2025-08-17/{urllib.parse.quote_plus(texto_busqueda)}/0/0"
    
    print(f"Texto original: {texto_busqueda}")
    print(f"URL con quote(): {url_normal}")
    print(f"URL con quote_plus(): {url_plus}")
    print()
    
    # Verificar codificación
    texto_codificado = urllib.parse.quote(texto_busqueda, safe='')
    print(f"Texto codificado: {texto_codificado}")
    print()
    
    # Verificar decodificación
    texto_decodificado = urllib.parse.unquote(texto_codificado)
    print(f"Texto decodificado: {texto_decodificado}")
    print(f"¿Coincide con original?: {texto_decodificado == texto_busqueda}")
    print()
    
    try:
        session = requests.Session()
        session.headers.update(ScrapingConfig.get_headers())
        
        print("Probando con urllib.parse.quote()...")
        response = session.get(url_normal, timeout=30)
        print(f"Status Code: {response.status_code}")
        print(f"Tamaño del contenido: {len(response.content)} bytes")
        
        # Verificar si hay diferencias con quote_plus
        print("\nProbando con urllib.parse.quote_plus()...")
        response2 = session.get(url_plus, timeout=30)
        print(f"Status Code: {response2.status_code}")
        print(f"Tamaño del contenido: {response2.content} bytes")
        
        # Comparar respuestas
        print(f"\n¿Las respuestas son iguales?: {response.content == response2.content}")
        
        # Analizar contenido de la primera respuesta
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar indicadores de resultados o errores
        texto_completo = soup.get_text().lower()
        
        # Buscar posibles mensajes de error o sin resultados
        indicadores_error = [
            'error', 'no encontrado', 'sin resultados', 'no se encontraron',
            'página no encontrada', '404', 'bad request', 'invalid'
        ]
        
        print("\n=== ANÁLISIS DE CONTENIDO ===")
        for indicador in indicadores_error:
            if indicador in texto_completo:
                print(f"Posible indicador de error encontrado: '{indicador}'")
        
        # Buscar elementos específicos de la página de búsqueda
        elementos_busqueda = [
            'buscador', 'jurisprudencia', 'relatoria', 'corte constitucional',
            'providencia', 'sentencia', 'tutela'
        ]
        
        print("\n=== ELEMENTOS DE LA PÁGINA ===")
        for elemento in elementos_busqueda:
            if elemento in texto_completo:
                print(f"Elemento encontrado: '{elemento}'")
        
        # Verificar si la página cargó correctamente
        title = soup.find('title')
        if title:
            print(f"\nTítulo de la página: {title.get_text()}")
        
        # Buscar meta tags o información adicional
        meta_description = soup.find('meta', {'name': 'description'})
        if meta_description:
            print(f"Meta descripción: {meta_description.get('content', 'Sin contenido')}")
        
        print("\n✅ Test específico completado exitosamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_specific_scraping()
