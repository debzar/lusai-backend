"""
Servicio middleware para la API de la Corte Constitucional de Colombia.
Consume directamente la API JSON oficial.
"""

import logging
import requests
import json
from typing import List, Dict, Any
from urllib.parse import quote_plus
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PalabraBusqueda(BaseModel):
    """Modelo para una palabra de búsqueda con posición explícita."""
    texto: str
    pos: int

class SearchRequest(BaseModel):
    """Modelo para la solicitud de búsqueda."""
    fecha_inicio: str
    fecha_fin: str
    palabra: str
    extra: str = ""
    pagina: int = 0
    # Campos para búsqueda compleja con orden explícito
    palabras_and: List[PalabraBusqueda] = []  # Palabras que deben aparecer (AND)
    palabras_or: List[PalabraBusqueda] = []   # Palabras alternativas (OR)
    palabras_not: List[PalabraBusqueda] = []  # Palabras a excluir (NOT)
    maxprov: int = 100
    slop: int = 1

# Los modelos Sentencia y SearchResponse se eliminan porque ahora 
# retornamos la respuesta directa de la API sin procesamiento

class CorteMiddleware:
    """Middleware para la API de la Corte Constitucional."""
    
    def __init__(self):
        self.base_url = "https://www.corteconstitucional.gov.co/relatoria/buscador_new/"
    
    async def buscar_sentencias(self, request: SearchRequest) -> dict:
        """
        Proxy directo a la API de la Corte Constitucional.
        Retorna la respuesta tal como viene de la API original, pero agrega URLs completas.
        """
        try:
            if not request.palabra.strip():
                return {
                    "error": "La palabra de búsqueda no puede estar vacía."
                }
            
            logger.info(f"🔍 Proxy request: '{request.palabra}' con {len(request.palabras_and)} palabras AND, {len(request.palabras_or)} palabras OR")
            
            # Construir URL de la API original
            api_url = self._build_url(request)
            logger.info(f"🌐 URL COMPLETA: {api_url}")  # Info para que se vea siempre
            
            # Hacer petición directa a la API original
            response = requests.get(api_url, timeout=30)
            response.raise_for_status()
            
            # Extraer JSON de la respuesta (maneja HTML mixto)
            json_data = self._extract_json(response.text)
            
            # Procesar la respuesta para agregar URLs completas
            processed_data = self._process_response(json_data)
            
            logger.info(f"✅ Proxy successful")
            
            # Retornar la respuesta procesada
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error HTTP: {e}")
            return {
                "error": f"Error de conexión: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error inesperado: {e}")
            return {
                "error": f"Error interno: {str(e)}"
            }
    
    def _build_url(self, request: SearchRequest) -> str:
        """Construye la URL de la API siguiendo el patrón exacto que funciona."""
        palabra_encoded = quote_plus(request.palabra)
        if request.extra:
            palabra_encoded = quote_plus(f"{request.palabra} {request.extra}")
        
        # Patrón exacto: ?searchOption=texto&fini=...&ffin=...&tw_And1=...&tw_And2=...&excluir=&buscar_por=...&maxprov=...&slop=...&accion=search&tipo=json
        url_parts = [
            f"{self.base_url}?searchOption=texto",
            f"fini={request.fecha_inicio}",
            f"ffin={request.fecha_fin}"
        ]
        
        # Agregar parámetros tw_And, tw_Or, tw_Not en orden de posición
        all_params = []
        
        # Recopilar todos los parámetros con sus posiciones
        for palabra_obj in request.palabras_and:
            if palabra_obj.texto.strip() and palabra_obj.pos > 0:
                all_params.append((palabra_obj.pos, f"tw_And{palabra_obj.pos}={quote_plus(palabra_obj.texto.strip())}"))
        
        for palabra_obj in request.palabras_or:
            if palabra_obj.texto.strip() and palabra_obj.pos > 0:
                all_params.append((palabra_obj.pos, f"tw_Or{palabra_obj.pos}={quote_plus(palabra_obj.texto.strip())}"))
        
        for palabra_obj in request.palabras_not:
            if palabra_obj.texto.strip() and palabra_obj.pos > 0:
                all_params.append((palabra_obj.pos, f"tw_Not{palabra_obj.pos}={quote_plus(palabra_obj.texto.strip())}"))
        
        # Ordenar por posición y agregar a la URL
        all_params.sort(key=lambda x: x[0])
        for _, param in all_params:
            url_parts.append(param)
        
        # Agregar parámetros finales en el orden exacto que funciona
        url_parts.extend([
            "excluir=",  # Parámetro vacío pero necesario
            f"buscar_por={palabra_encoded}",
            f"maxprov={request.maxprov}",
            f"slop={request.slop}",
            "accion=search",
            "tipo=json"
        ])
        
        return "&".join(url_parts)
    
    def _extract_json(self, content: str) -> dict:
        """Extrae el JSON de una respuesta que puede contener HTML."""
        json_start = content.find('{')
        if json_start == -1:
            raise ValueError("No se encontró JSON en la respuesta")
        
        json_content = content[json_start:]
        return json.loads(json_content)
    
    def _process_response(self, data: dict) -> dict:
        """
        Procesa la respuesta de la API para agregar URLs completas.
        """
        try:
            # Crear una copia de los datos para no modificar el original
            processed_data = data.copy()
            
            # Procesar los hits para agregar URLs completas
            if 'data' in processed_data and 'hits' in processed_data['data']:
                hits = processed_data['data']['hits']
                if 'hits' in hits:
                    for hit in hits['hits']:
                        if '_source' in hit:
                            source = hit['_source']
                            # Construir URL completa si existe rutahtml
                            if 'rutahtml' in source and source['rutahtml']:
                                ruta_html = source['rutahtml']
                                url_completa = f"https://www.corteconstitucional.gov.co/relatoria/{ruta_html}"
                                # Agregar el campo url_html al _source
                                source['url_html'] = url_completa
                                logger.debug(f"🔗 URL construida: {url_completa}")
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error procesando respuesta: {e}")
            # Si hay error, retornar los datos originales
            return data
