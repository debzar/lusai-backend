"""
Rutas para el generador de prompts jurisprudenciales.
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.services.prompt_generator import PromptGenerator, PromptRequest
from app.config import settings

router = APIRouter(prefix="/prompt", tags=["prompt-generator"])

@router.post("/generate-url")
async def generate_search_url(
    request: PromptRequest,
    x_openai_api_key: Optional[str] = Header(None, description="API Key de OpenAI")
):
    """
    Genera una URL de búsqueda jurisprudencial basada en un prompt en lenguaje natural.
    
    **Ejemplo de uso:**
    ```json
    {
      "prompt": "Buscame un caso de una menor de edad que le limiten el derecho a la educación en un colegio para adultos desde el año 2000 hasta la actualidad."
    }
    ```
    
    **Respuesta:**
    ```json
    {
      "url": "https://www.corteconstitucional.gov.co/relatoria/buscador_new/?searchOption=texto&fini=2000-01-01&ffin=2025-08-26&tw_And1=educacion&tw_And2=menor&excluir=&buscar_por=tutela&maxprov=100&slop=1&accion=search&tipo=json",
      "razonamiento": "Se extrajo 'tutela' como palabra principal ya que es el mecanismo típico para proteger derechos fundamentales. Las palabras clave 'educacion' y 'menor' son centrales en la consulta.",
      "palabras_clave": {
        "buscar_por": ["tutela"],
        "tw_and": ["educacion", "menor"],
        "excluir": []
      }
    }
    ```
    
    - **prompt**: Consulta en lenguaje natural
    - **x_openai_api_key**: API Key de OpenAI (opcional - se usa automáticamente desde .env si está configurada)
    """
    try:
        # Usar API key del header, del request, o de la configuración (en ese orden de prioridad)
        api_key = x_openai_api_key or request.api_key or settings.OPENAI_API_KEY
        
        if not api_key:
            raise HTTPException(
                status_code=400, 
                detail="Se requiere una API key de OpenAI. Configúrala en el archivo .env con OPENAI_API_KEY o pásala en el header X-OpenAI-API-Key"
            )
        
        generator = PromptGenerator(api_key)
        request.api_key = api_key
        
        response = await generator.generate_search_url(request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando URL: {str(e)}")

@router.post("/search-and-analyze")
async def search_and_analyze(
    request: PromptRequest,
    x_openai_api_key: Optional[str] = Header(None, description="API Key de OpenAI")
):
    """
    Genera URL, busca en la API de la Corte y analiza resultados para encontrar los 7 más útiles.
    
    **Ejemplo de uso:**
    ```json
    {
      "prompt": "Buscame un caso de una menor de edad que le limiten el derecho a la educación en un colegio para adultos desde el año 2000 hasta la actualidad."
    }
    ```
    
    **Respuesta:**
    ```json
    {
      "url_generada": "https://www.corteconstitucional.gov.co/relatoria/buscador_new/?...",
      "razonamiento": "Explicación de las palabras clave elegidas",
      "palabras_clave": {
        "buscar_por": ["tutela"],
        "tw_and": ["educacion", "menor"],
        "excluir": []
      },
      "total_resultados": 689,
      "resultados_analizados": [
        {
          "sentencia": "T-040/25",
          "fecha": "2025-02-05",
          "tema": "DERECHO A LA EDUCACIÓN INCLUSIVA DE NIÑOS, NIÑAS Y ADOLESCENTES",
          "sintesis": "En este caso se atribuye la vulneración de derechos fundamentales...",
          "magistrados": ["Jorge Enrique Ibáñez Najar"],
          "expediente": "T-10389113",
          "url_html": "https://www.corteconstitucional.gov.co/relatoria/2025/T-040-25.htm",
          "score": 18.736814,
          "razon_seleccion": "Caso muy relevante sobre derecho a la educación de menores con problemas de acoso escolar"
        }
      ]
    }
    ```
    
    - **prompt**: Consulta en lenguaje natural
    - **x_openai_api_key**: API Key de OpenAI (opcional - se usa automáticamente desde .env si está configurada)
    """
    try:
        # Usar API key del header, del request, o de la configuración (en ese orden de prioridad)
        api_key = x_openai_api_key or request.api_key or settings.OPENAI_API_KEY
        
        if not api_key:
            raise HTTPException(
                status_code=400, 
                detail="Se requiere una API key de OpenAI. Configúrala en el archivo .env con OPENAI_API_KEY o pásala en el header X-OpenAI-API-Key"
            )
        
        generator = PromptGenerator(api_key)
        request.api_key = api_key
        
        response = await generator.search_and_analyze(request)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda y análisis: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Verifica el estado del servicio de generación de prompts.
    """
    return {
        "status": "healthy",
        "service": "prompt-generator",
        "message": "Servicio de generación de prompts jurisprudenciales operativo"
    }
