"""
Utilidades para el servicio de scraping.
"""

import re
import urllib.parse
from typing import Optional
from .config import ScrapingConfig

def build_search_url(fecha_inicio: str, fecha_fin: str, palabra: str, extra: str = "", pagina: int = 0) -> str:
    """Construye la URL de búsqueda para la Corte Constitucional."""
    palabra_encoded = urllib.parse.quote(palabra, safe='')
    return f"{ScrapingConfig.SEARCH_URL}/{fecha_inicio}/{fecha_fin}/{palabra_encoded}/{extra}/{pagina}"

def extract_sentencia_number(texto: str) -> Optional[str]:
    """Extrae el número de sentencia del texto."""
    match = re.search(ScrapingConfig.SENTENCIA_PATTERN, texto)
    return match.group(1) if match else None

def extract_tema_from_text(texto: str, palabra_busqueda: str) -> str:
    """Extrae el tema del texto basándose en la palabra de búsqueda."""
    try:
        # Buscar líneas que contengan palabras clave relacionadas con temas
        lineas = texto.split('\n')
        palabras_clave = ['tema:', 'materia:', 'asunto:', 'derecho', 'constitucional']
        
        for linea in lineas:
            linea_lower = linea.lower().strip()
            if any(palabra in linea_lower for palabra in palabras_clave):
                # Limpiar y extraer el tema
                tema = re.sub(r'^(tema|materia|asunto):\s*', '', linea, flags=re.IGNORECASE)
                if tema and len(tema) > 5:
                    return tema[:200]  # Limitar longitud
        
        # Si no encontramos tema específico, usar la palabra de búsqueda
        return f"Búsqueda relacionada con: {palabra_busqueda}"
        
    except Exception:
        return f"Búsqueda relacionada con: {palabra_busqueda}"

def extract_subtema_from_text(texto: str, palabra_busqueda: str) -> str:
    """Extrae el subtema del texto."""
    try:
        # Buscar líneas que parezcan subtemas
        lineas = texto.split('\n')
        
        for i, linea in enumerate(lineas):
            linea_lower = linea.lower().strip()
            if any(palabra in linea_lower for palabra in ['subtema:', 'descripción:', 'resumen:']):
                if i + 1 < len(lineas):
                    subtema = lineas[i + 1].strip()
                    if subtema and len(subtema) > 5:
                        return subtema[:300]  # Limitar longitud
        
        # Si no encontramos subtema específico, usar parte del texto
        palabras = texto.split()
        if len(palabras) > 10:
            # Tomar una porción del texto como subtema
            inicio = max(0, len(palabras) // 3)
            fin = min(len(palabras), inicio + 20)
            subtema = ' '.join(palabras[inicio:fin])
            return subtema[:300]
        
        return ""
        
    except Exception:
        return ""

def normalize_url(url: str) -> str:
    """Normaliza una URL para asegurar que tenga el protocolo correcto."""
    if not url:
        return ""
    
    url = url.strip()
    
    if url.startswith('http://') or url.startswith('https://'):
        return url
    elif url.startswith('//'):
        return f"https:{url}"
    elif url.startswith('/'):
        return f"{ScrapingConfig.BASE_URL}{url}"
    else:
        return f"{ScrapingConfig.BASE_URL}/{url}"

def generate_sentencia_urls(titulo: str, año: str) -> tuple[str, str]:
    """Genera URLs HTML y PDF para una sentencia."""
    titulo_clean = titulo.replace('/', '-')
    url_html = f"{ScrapingConfig.BASE_URL}/relatoria/{año}/{titulo_clean}.htm"
    url_pdf = f"{ScrapingConfig.BASE_URL}/relatoria/{año}/{titulo_clean}.pdf"
    return url_html, url_pdf
