"""
Paquete de servicios de scraping para la Corte Constitucional de Colombia.
"""

from .scraper import ScrapingService
from .models import SearchRequest, SearchResult, Sentencia, ScrapingResponse

# Importar tests para fácil acceso
from .tests import test_scraping_package, test_sync_functions, test_specific_scraping

__all__ = [
    'ScrapingService',
    'SearchRequest', 
    'SearchResult',
    'Sentencia',
    'ScrapingResponse',
    # Tests
    'test_scraping_package',
    'test_sync_functions',
    'test_specific_scraping'
]
