"""
Servicio generador de prompts para búsqueda jurisprudencial usando OpenAI.
"""

import logging
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from openai import OpenAI
from pydantic import BaseModel
from urllib.parse import quote_plus
from app.config import settings

logger = logging.getLogger(__name__)

class PromptRequest(BaseModel):
    """Modelo para la solicitud de generación de prompt."""
    prompt: str
    api_key: Optional[str] = None  # API key de OpenAI (opcional si está en config)

class SearchUrlResponse(BaseModel):
    """Modelo para la respuesta de URL generada."""
    url: str
    razonamiento: str
    palabras_clave: Dict[str, List[str]]

class PromptGenerator:
    """Generador de URLs de búsqueda jurisprudencial usando OpenAI."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key or settings.OPENAI_API_KEY
        self.base_url = "https://www.corteconstitucional.gov.co/relatoria/buscador_new/"
        
    def _get_openai_client(self, api_key: Optional[str] = None) -> OpenAI:
        """Obtiene el cliente de OpenAI con la API key."""
        key = api_key or self.openai_api_key
        if not key:
            raise ValueError("Se requiere una API key de OpenAI")
        return OpenAI(api_key=key)
    
    async def generate_search_url(self, request: PromptRequest) -> SearchUrlResponse:
        """
        Genera una URL de búsqueda jurisprudencial basada en un prompt en lenguaje natural.
        """
        try:
            logger.info(f"🤖 Generando URL para prompt: '{request.prompt[:100]}...'")
            
            # Obtener fecha actual
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            
            # Crear el prompt para OpenAI
            system_prompt = self._create_system_prompt(fecha_actual)
            user_prompt = f"Prompt del usuario: \"{request.prompt}\""
            
            # Llamar a OpenAI
            client = self._get_openai_client(request.api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",  # Modelo más económico pero eficiente
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Baja temperatura para respuestas más consistentes
                max_tokens=1000
            )
            
            # Parsear la respuesta
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"🤖 Respuesta de OpenAI: {response_text}")
            
            # Extraer JSON de la respuesta
            json_response = self._extract_json_from_response(response_text)
            
            # Validar y crear respuesta
            search_response = SearchUrlResponse(**json_response)
            
            logger.info(f"✅ URL generada exitosamente")
            return search_response
            
        except Exception as e:
            logger.error(f"Error generando URL: {e}")
            raise
    
    async def search_and_analyze(self, request: PromptRequest) -> Dict[str, Any]:
        """
        Genera URL, hace búsqueda y analiza resultados para encontrar los 7 más útiles.
        """
        try:
            # 1. Generar URL
            url_response = await self.generate_search_url(request)
            logger.info(f"🔍 URL generada: {url_response.url}")
            
            # 2. Hacer búsqueda en la API de la Corte
            search_results = await self._search_corte_api(url_response.url)
            
            # 3. Analizar resultados con OpenAI
            if search_results and 'data' in search_results and 'hits' in search_results['data']:
                hits = search_results['data']['hits']['hits']
                if hits:
                    analyzed_results = await self._analyze_results_with_openai(
                        request.prompt, hits, request.api_key
                    )
                    
                    return {
                        "url_generada": url_response.url,
                        "razonamiento": url_response.razonamiento,
                        "palabras_clave": url_response.palabras_clave,
                        "total_resultados": search_results['data']['hits']['total']['value'],
                        "resultados_analizados": analyzed_results
                    }
            
            return {
                "url_generada": url_response.url,
                "razonamiento": url_response.razonamiento,
                "palabras_clave": url_response.palabras_clave,
                "total_resultados": 0,
                "resultados_analizados": [],
                "mensaje": "No se encontraron resultados para la búsqueda"
            }
            
        except Exception as e:
            logger.error(f"Error en búsqueda y análisis: {e}")
            raise
    
    def _create_system_prompt(self, fecha_actual: str) -> str:
        """Crea el prompt del sistema para OpenAI."""
        return f"""
Eres un experto en búsqueda jurisprudencial de la Corte Constitucional de Colombia.

INFORMACIÓN CONTEXTUAL:
- Formato de fecha: YYYY-MM-DD
- Fecha de hoy: {fecha_actual}
- URL base: {self.base_url}

TU TAREA:
Analiza el prompt del usuario y extrae información para generar una URL de búsqueda jurisprudencial.

PARÁMETROS A EXTRAER:
1. **buscar_por**: UNA palabra clave jurídica principal (ej: tutela, demanda, acción, constitucionalidad)
2. **tw_And1, tw_And2, tw_And3...**: Palabras clave específicas que DEBEN aparecer en las sentencias
3. **excluir**: Palabras a excluir si detectas intención de exclusión en el prompt
4. **fini**: Fecha de inicio (por defecto 1992-01-01 si no se especifica)
5. **ffin**: Fecha de fin (por defecto fecha actual si no se especifica)

REGLAS:
- Extrae máximo 6 palabras para tw_And (tw_And1 hasta tw_And6)
- Prioriza términos jurídicos específicos
- Si detectas exclusiones explícitas, úsalas en el parámetro excluir
- Mantén el orden lógico de importancia en las palabras AND

FORMATO DE RESPUESTA (JSON):
{{
  "url": "URL_COMPLETA_GENERADA",
  "razonamiento": "Explicación breve de las palabras clave elegidas y por qué",
  "palabras_clave": {{
    "buscar_por": ["palabra_principal"],
    "tw_and": ["palabra1", "palabra2", "palabra3"],
    "excluir": ["palabra_excluida"] o []
  }}
}}

EJEMPLO DE URL:
{self.base_url}?searchOption=texto&fini=2000-01-01&ffin={fecha_actual}&tw_And1=educacion&tw_And2=menor&excluir=&buscar_por=tutela&maxprov=100&slop=1&accion=search&tipo=json

Responde ÚNICAMENTE con el JSON, sin texto adicional.
"""

    def _extract_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """Extrae JSON de la respuesta de OpenAI."""
        try:
            # Buscar JSON en la respuesta
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No se encontró JSON en la respuesta")
            
            json_str = response_text[json_start:json_end]
            return json.loads(json_str)
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parseando JSON: {e}")
            logger.error(f"Respuesta problemática: {response_text}")
            raise ValueError(f"Respuesta de OpenAI no contiene JSON válido: {str(e)}")
    
    async def _search_corte_api(self, url: str) -> Dict[str, Any]:
        """Hace búsqueda en la API de la Corte Constitucional."""
        try:
            logger.info(f"🔍 Buscando en API de Corte: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Extraer JSON de la respuesta
            json_start = response.text.find('{')
            if json_start == -1:
                raise ValueError("Respuesta de la API no contiene JSON")
            
            json_content = response.text[json_start:]
            return json.loads(json_content)
            
        except Exception as e:
            logger.error(f"Error buscando en API de Corte: {e}")
            raise
    
    async def _analyze_results_with_openai(self, original_prompt: str, hits: List[Dict], api_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Analiza los resultados con OpenAI para encontrar los más útiles."""
        try:
            # Preparar datos de sentencias para análisis
            sentences_data = []
            for i, hit in enumerate(hits[:15]):  # Analizar máximo 15 resultados
                source = hit.get('_source', {})
                sentences_data.append({
                    "indice": i + 1,
                    "sentencia": source.get('prov_sentencia', 'N/A'),
                    "fecha": source.get('prov_f_sentencia', 'N/A'),
                    "tema": source.get('prov_tema', 'N/A')[:200] + '...' if len(source.get('prov_tema', '')) > 200 else source.get('prov_tema', 'N/A'),
                    "sintesis": source.get('prov_sintesis', 'N/A')[:300] + '...' if len(source.get('prov_sintesis', '')) > 300 else source.get('prov_sintesis', 'N/A'),
                    "score": hit.get('_score', 0)
                })
            
            # Crear prompt para análisis
            analysis_prompt = f"""
Analiza estas sentencias de la Corte Constitucional y selecciona las 7 MÁS ÚTILES para responder a esta consulta:

CONSULTA ORIGINAL: "{original_prompt}"

SENTENCIAS ENCONTRADAS:
{json.dumps(sentences_data, indent=2, ensure_ascii=False)}

CRITERIOS DE SELECCIÓN:
1. Relevancia temática con la consulta
2. Claridad y completitud de la síntesis
3. Fecha de la sentencia (más recientes son preferibles)
4. Score de relevancia

RESPONDE CON UN JSON:
{{
  "seleccionadas": [
    {{
      "indice": 1,
      "razon": "Explicación breve de por qué es útil para la consulta"
    }}
  ]
}}

Selecciona exactamente 7 sentencias. Responde ÚNICAMENTE con el JSON.
"""

            client = self._get_openai_client(api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis jurisprudencial. Analiza y selecciona las sentencias más relevantes."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            # Parsear respuesta
            analysis_response = self._extract_json_from_response(response.choices[0].message.content.strip())
            
            # Construir resultados finales
            final_results = []
            for selected in analysis_response.get('seleccionadas', [])[:7]:
                indice = selected.get('indice', 1) - 1  # Convertir a índice 0-based
                if 0 <= indice < len(hits):
                    hit = hits[indice]
                    source = hit.get('_source', {})
                    
                    # Construir URL completa si existe rutahtml
                    url_html = None
                    if 'rutahtml' in source and source['rutahtml']:
                        url_html = f"https://www.corteconstitucional.gov.co/relatoria/{source['rutahtml']}"
                    
                    final_results.append({
                        "sentencia": source.get('prov_sentencia', 'N/A'),
                        "fecha": source.get('prov_f_sentencia', 'N/A'),
                        "tema": source.get('prov_tema', 'N/A'),
                        "sintesis": source.get('prov_sintesis', 'N/A'),
                        "magistrados": source.get('prov_magistrados', []),
                        "expediente": source.get('prov_expediente', 'N/A'),
                        "url_html": url_html,
                        "score": hit.get('_score', 0),
                        "razon_seleccion": selected.get('razon', 'N/A')
                    })
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error analizando resultados con OpenAI: {e}")
            # Si falla el análisis, retornar los primeros 7 resultados
            return self._get_top_results_fallback(hits[:7])
    
    def _get_top_results_fallback(self, hits: List[Dict]) -> List[Dict[str, Any]]:
        """Fallback para obtener los primeros resultados si falla el análisis con OpenAI."""
        results = []
        for hit in hits:
            source = hit.get('_source', {})
            
            # Construir URL completa si existe rutahtml
            url_html = None
            if 'rutahtml' in source and source['rutahtml']:
                url_html = f"https://www.corteconstitucional.gov.co/relatoria/{source['rutahtml']}"
            
            results.append({
                "sentencia": source.get('prov_sentencia', 'N/A'),
                "fecha": source.get('prov_f_sentencia', 'N/A'),
                "tema": source.get('prov_tema', 'N/A'),
                "sintesis": source.get('prov_sintesis', 'N/A'),
                "magistrados": source.get('prov_magistrados', []),
                "expediente": source.get('prov_expediente', 'N/A'),
                "url_html": url_html,
                "score": hit.get('_score', 0),
                "razon_seleccion": "Seleccionado por score de relevancia (análisis automático falló)"
            })
        
        return results
