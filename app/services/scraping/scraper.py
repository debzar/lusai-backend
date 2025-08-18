"""
Servicio principal de scraping para la Corte Constitucional de Colombia.
"""

import logging
import re
import asyncio
import concurrent.futures
from typing import List, Optional
from .models import SearchRequest, SearchResult, Sentencia, ScrapingResponse
from .config import ScrapingConfig
from .utils import build_search_url
from .extractors import SeleniumExtractor

logger = logging.getLogger(__name__)

class ScrapingService:
    """Servicio principal de scraping."""
    
    def __init__(self):
        self.selenium_extractor = SeleniumExtractor()
    
    async def search_sentencias(self, request: SearchRequest) -> ScrapingResponse:
        """
        Busca sentencias en la Corte Constitucional de Colombia.
        
        Args:
            request: Solicitud de búsqueda con todos los parámetros
            
        Returns:
            Respuesta con los resultados de la búsqueda
        """
        try:
            logger.info(f"Buscando sentencias: {request.fecha_inicio} a {request.fecha_fin}, palabra: '{request.palabra}', página: {request.pagina}")
            
            # Construir URL de búsqueda
            url = build_search_url(
                request.fecha_inicio,
                request.fecha_fin,
                request.palabra,
                request.extra,
                request.pagina
            )
            
            # Estrategia 1: Intentar con Selenium para contenido dinámico
            resultados = await self._try_selenium_extraction(url, request.palabra)
            if resultados:
                logger.info(f"Encontrados {len(resultados)} resultados con Selenium")
                return self._build_response(resultados, "Selenium")
            
            # Si Selenium falla, retornar respuesta vacía
            logger.warning("No se pudieron extraer resultados reales")
            return self._build_response([], "Error", "No se pudieron extraer resultados de la Corte Constitucional")
            
        except Exception as e:
            logger.error(f"Error en scraping: {e}")
            return self._build_response([], "Error", f"Error durante el scraping: {str(e)}")
    
    async def _try_selenium_extraction(self, url: str, palabra: str) -> List[SearchResult]:
        """Intenta extracción con Selenium."""
        try:
            logger.info("🔄 Intentando extracción con Selenium...")
            # Ejecutar en un thread separado para no bloquear
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                resultado = await loop.run_in_executor(
                    executor, 
                    self.selenium_extractor.extract, 
                    url, 
                    palabra
                )
            logger.info(f"✅ Selenium completado, {len(resultado)} resultados")
            return resultado
        except Exception as e:
            logger.warning(f"❌ Selenium falló: {e}")
            return []
    

    
    def _build_response(self, resultados: List[SearchResult], metodo: str, nota: Optional[str] = None) -> ScrapingResponse:
        """Construye la respuesta del servicio."""
        return ScrapingResponse(
            status="success",
            total_resultados=len(resultados),
            resultados=resultados,
            nota=nota or f"Resultados extraídos usando {metodo}"
        )
    

