"""
Configuración para el servicio de scraping de la Corte Constitucional.
"""

import os
from typing import Dict, Any

class ScrapingConfig:
    """Configuración del servicio de scraping."""
    
    # URLs base
    BASE_URL = "https://www.corteconstitucional.gov.co"
    SEARCH_URL = f"{BASE_URL}/relatoria/buscador-jurisprudencia/texto"
    
    # Timeouts (en segundos)
    SELENIUM_TIMEOUT = 30
    SELENIUM_PAGE_LOAD_TIMEOUT = 30
    SELENIUM_WAIT_TIMEOUT = 20
    REQUESTS_TIMEOUT = 30
    API_TIMEOUT = 15
    
    # Delays y esperas
    SELENIUM_RENDER_DELAY = 5  # Tiempo extra para que Angular renderice
    RATE_LIMIT_DELAY = 1  # Delay entre requests para evitar bloqueos
    
    # Configuración de Chrome/Selenium
    CHROME_OPTIONS = {
        "headless": True,
        "no_sandbox": True,
        "disable_dev_shm_usage": True,
        "disable_gpu": True,
        "window_size": "1920,1080",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    
    # Headers para requests
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    # Headers para APIs
    API_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Referer': 'https://www.corteconstitucional.gov.co/relatoria/buscador-jurisprudencia',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    # Endpoints de API a probar
    API_ENDPOINTS = [
        f"{BASE_URL}/api/relatoria/buscar",
        f"{BASE_URL}/relatoria/api/buscar",
        f"{BASE_URL}/services/buscar",
        f"{BASE_URL}/api/jurisprudencia",
        f"{BASE_URL}/relatoria/api/jurisprudencia"
    ]
    
    # Patrones de búsqueda para sentencias
    SENTENCIA_PATTERNS = [
        r'([TCSU]+-?\d{1,4}[/-]\d{2,4})',  # T-322/25, C-123/20, SU-456/19
        r'(AUTO-?\d{1,4}[/-]\d{2,4})',     # AUTO-100/20
        r'(\d{1,4}[/-]\d{2,4})',            # 322/25, 123/20
    ]
    
    # Selectores CSS para diferentes patrones de resultados
    CSS_SELECTORS = {
        "tabla_resultados": "table tbody tr",
        "clases_resultado": [".resultado", ".sentencia", ".providencia"],
        "atributos_data": "[data-resultado]",
        "enlaces_relatoria": "a[href*='relatoria']",
        "elementos_estructurados": [
            ".resultado",
            ".sentencia", 
            ".providencia",
            "[data-resultado]"
        ]
    }
    
    # Límites de resultados
    MAX_RESULTADOS_POR_PAGINA = 25
    MAX_RESULTADOS_TOTAL = 100
    MAX_RESULTADOS_TEXTO_LIBRE = 10
    
    # Configuración de logging
    LOG_LEVEL = os.getenv("SCRAPING_LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configuración de reintentos
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    # Configuración de proxies (opcional)
    USE_PROXY = os.getenv("SCRAPING_USE_PROXY", "false").lower() == "true"
    PROXY_CONFIG = {
        "http": os.getenv("SCRAPING_HTTP_PROXY"),
        "https": os.getenv("SCRAPING_HTTPS_PROXY")
    } if USE_PROXY else None
    
    # Configuración de caché
    ENABLE_CACHE = os.getenv("SCRAPING_ENABLE_CACHE", "true").lower() == "true"
    CACHE_TTL = int(os.getenv("SCRAPING_CACHE_TTL", "3600"))  # 1 hora por defecto
    
    # Configuración de validación
    VALIDATE_URLS = True
    VALIDATE_CONTENT = True
    MIN_CONTENT_LENGTH = 100
    
    # Configuración de extracción de texto
    EXTRACCION_CONFIG = {
        "max_tema_length": 200,
        "max_subtema_length": 300,
        "contexto_antes": 200,
        "contexto_despues": 400,
        "min_texto_length": 10
    }
    
    @classmethod
    def get_chrome_options(cls) -> Dict[str, Any]:
        """Obtiene las opciones de Chrome para Selenium."""
        return cls.CHROME_OPTIONS.copy()
    
    @classmethod
    def get_headers(cls, use_api: bool = False) -> Dict[str, str]:
        """Obtiene los headers apropiados según el tipo de request."""
        if use_api:
            return cls.API_HEADERS.copy()
        return cls.DEFAULT_HEADERS.copy()
    
    @classmethod
    def get_timeout(cls, method: str) -> int:
        """Obtiene el timeout apropiado según el método."""
        timeouts = {
            "selenium": cls.SELENIUM_TIMEOUT,
            "selenium_page": cls.SELENIUM_PAGE_LOAD_TIMEOUT,
            "selenium_wait": cls.SELENIUM_WAIT_TIMEOUT,
            "requests": cls.REQUESTS_TIMEOUT,
            "api": cls.API_TIMEOUT
        }
        return timeouts.get(method, cls.REQUESTS_TIMEOUT)
    
    @classmethod
    def is_production(cls) -> bool:
        """Determina si estamos en producción."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    @classmethod
    def get_cache_config(cls) -> Dict[str, Any]:
        """Obtiene la configuración de caché."""
        if not cls.ENABLE_CACHE:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "ttl": cls.CACHE_TTL,
            "max_size": int(os.getenv("SCRAPING_CACHE_MAX_SIZE", "1000"))
        }

# Instancia global de configuración
config = ScrapingConfig()
