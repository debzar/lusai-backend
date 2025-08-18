"""
Tests para el paquete de scraping.
"""

from .test_scraping_package import test_scraping_package, test_sync_functions
from .test_scraping_specific import test_specific_scraping

__all__ = [
    'test_scraping_package',
    'test_sync_functions', 
    'test_specific_scraping'
]
