#!/usr/bin/env python3
"""
Test específico para probar la URL de búsqueda de la Corte Constitucional usando Selenium.
"""

import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from ..config import ScrapingConfig

def test_specific_scraping():
    """Prueba la URL específica de búsqueda usando Selenium."""
    
    print("🧪 Probando URL específica de búsqueda con Selenium...")
    print("=" * 60)
    
    # Probando la URL específica que proporcionaste
    texto_busqueda = "Marcela como agente oficiosa de su nieta Sara en contra de la Secretaría de Educación"
    
    # Construir URL de búsqueda
    url = f"https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia/texto/1992-01-01/2025-08-17/{urllib.parse.quote(texto_busqueda, safe='')}/0/0"
    
    print(f"Texto original: {texto_busqueda}")
    print(f"URL de búsqueda: {url}")
    print()
    
    # Verificar codificación
    texto_codificado = urllib.parse.quote(texto_busqueda, safe='')
    print(f"Texto codificado: {texto_codificado}")
    
    # Verificar decodificación
    texto_decodificado = urllib.parse.unquote(texto_codificado)
    print(f"Texto decodificado: {texto_decodificado}")
    print(f"¿Coincide con original?: {texto_decodificado == texto_busqueda}")
    print()
    
    driver = None
    try:
        print("🚀 Iniciando Selenium...")
        
        # Configurar Chrome
        chrome_options = Options()
        for key, value in ScrapingConfig.get_chrome_options().items():
            chrome_options.add_argument(f"--{key}={value}")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(ScrapingConfig.SELENIUM_PAGE_LOAD_TIMEOUT)
        
        print("🌐 Navegando a la URL...")
        driver.get(url)
        
        # Esperar a que la página cargue
        wait = WebDriverWait(driver, ScrapingConfig.SELENIUM_WAIT_TIMEOUT)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        # Tiempo extra para que Angular renderice
        import time
        time.sleep(ScrapingConfig.SELENIUM_RENDER_DELAY)
        
        print("📄 Analizando contenido de la página...")
        
        # Obtener información básica de la página
        title = driver.title
        print(f"📋 Título de la página: {title}")
        
        # Obtener URL actual (por si hay redirecciones)
        current_url = driver.current_url
        print(f"🔗 URL actual: {current_url}")
        
        # Analizar contenido de la página
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        print(f"📊 Tamaño del contenido: {len(body_text)} caracteres")
        
        # Buscar indicadores de resultados o errores
        indicadores_error = [
            'error', 'no encontrado', 'sin resultados', 'no se encontraron',
            'página no encontrada', '404', 'bad request', 'invalid'
        ]
        
        print("\n=== ANÁLISIS DE CONTENIDO ===")
        for indicador in indicadores_error:
            if indicador in body_text:
                print(f"⚠️ Posible indicador de error encontrado: '{indicador}'")
        
        # Buscar elementos específicos de la página de búsqueda
        elementos_busqueda = [
            'buscador', 'jurisprudencia', 'relatoria', 'corte constitucional',
            'providencia', 'sentencia', 'tutela'
        ]
        
        print("\n=== ELEMENTOS DE LA PÁGINA ===")
        for elemento in elementos_busqueda:
            if elemento in body_text:
                print(f"✅ Elemento encontrado: '{elemento}'")
        
        # Buscar patrones de sentencias
        import re
        sentencias_encontradas = re.findall(ScrapingConfig.SENTENCIA_PATTERN, body_text)
        if sentencias_encontradas:
            print(f"\n📜 Sentencias encontradas: {len(sentencias_encontradas)}")
            for i, sentencia in enumerate(sentencias_encontradas[:5], 1):
                print(f"   {i}. {sentencia}")
        else:
            print("\n📜 No se encontraron patrones de sentencias")
        
        # Verificar si hay elementos de interfaz de usuario
        try:
            # Buscar elementos que podrían indicar que la página cargó correctamente
            elementos_ui = driver.find_elements(By.CSS_SELECTOR, "input, button, table, .resultado, .sentencia")
            print(f"\n🎨 Elementos de UI encontrados: {len(elementos_ui)}")
            
            if elementos_ui:
                print("✅ La página parece haber cargado correctamente con elementos de interfaz")
            else:
                print("⚠️ No se encontraron elementos de interfaz de usuario")
                
        except Exception as e:
            print(f"⚠️ Error al buscar elementos de UI: {e}")
        
        print("\n✅ Test específico completado exitosamente!")
        return True
        
    except TimeoutException:
        print("⏰ Timeout: La página tardó demasiado en cargar")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            print("🧹 Cerrando navegador...")
            driver.quit()

if __name__ == "__main__":
    test_specific_scraping()
