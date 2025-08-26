"""
Configuración para el servicio de scraping.
"""

import os
from typing import Dict, Any

class ScrapingConfig:
    """Configuración del servicio de scraping."""
    
    # URLs base
    BASE_URL = "https://www.corteconstitucional.gov.co"
    SEARCH_URL = f"{BASE_URL}/relatoria/buscador-jurisprudencia/"
    
    # Timeouts para Selenium (en segundos)
    SELENIUM_TIMEOUT = 30
    SELENIUM_PAGE_LOAD_TIMEOUT = 30
    SELENIUM_WAIT_TIMEOUT = 20
    
    # Delays y esperas
    SELENIUM_RENDER_DELAY = 5  # Tiempo extra para que Angular renderice
    
    # Configuración de Chrome/Seleniumhttps://www.corteconstitucional.gov.co
    CHROME_OPTIONS = {
        "headless": True,
        "no_sandbox": True,
        "disable_dev_shm_usage": True,
        "disable_gpu": True,
        "window_size": "1920,1080",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    
    # Límites de resultados
    MAX_RESULTS_PER_PAGE = 25
    MAX_RESULTS_TOTAL = 100
    
    # Patrones de búsqueda
    SENTENCIA_PATTERN = r'([TCSU]+-?\d{1,4}[/-]\d{2,4})'
    
    @classmethod
    def get_chrome_options(cls) -> Dict[str, Any]:
        """Obtiene las opciones de Chrome para Selenium."""
        return cls.CHROME_OPTIONS.copy()
