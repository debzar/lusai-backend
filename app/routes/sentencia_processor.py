"""
Rutas para el procesamiento de sentencias de la Corte Constitucional.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from pydantic import BaseModel, HttpUrl

from app.services.sentencia_processor import SentenciaProcessor
from app.db.database import get_db

router = APIRouter(prefix="/sentencias", tags=["sentencias"])

class ProcessSentenciaRequest(BaseModel):
    """Modelo para procesar una sentencia desde URL."""
    url: str
    metadata: Dict[str, Any] = {}

class ProcessFromSearchResultRequest(BaseModel):
    """Modelo para procesar una sentencia desde resultado de búsqueda."""
    search_result: Dict[str, Any]

@router.post("/process-from-url")
async def process_sentencia_from_url(
    request: ProcessSentenciaRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Procesa una sentencia desde su URL, descarga el HTML, extrae el texto y la indexa.
    
    **Ejemplo de uso:**
    ```json
    {
      "url": "https://www.corteconstitucional.gov.co/relatoria/2025/T-040-25.htm",
      "metadata": {
        "sentencia": "T-040/25",
        "tema": "DERECHO A LA EDUCACIÓN INCLUSIVA"
      }
    }
    ```
    
    **Respuesta:**
    ```json
    {
      "document_id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "sentencia_T-040-25.html",
      "url": "https://supabase.url/storage/...",
      "original_url": "https://www.corteconstitucional.gov.co/relatoria/2025/T-040-25.htm",
      "text_length": 45230,
      "text_preview": "SENTENCIA T-040/25...",
      "indexing_result": {
        "chunks_indexed": 23,
        "embedding_model": "text-embedding-3-small"
      },
      "metadata": {
        "sentencia": "T-040/25",
        "tema": "DERECHO A LA EDUCACIÓN INCLUSIVA"
      }
    }
    ```
    
    - **url**: URL completa de la sentencia en el sitio de la Corte Constitucional
    - **metadata**: Metadatos adicionales de la sentencia (opcional)
    """
    try:
        processor = SentenciaProcessor()
        result = await processor.process_sentencia_from_url(
            db=db,
            sentencia_url=request.url,
            metadata=request.metadata
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando sentencia: {str(e)}")

@router.post("/process-from-search-result")
async def process_sentencia_from_search_result(
    request: ProcessFromSearchResultRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Procesa una sentencia desde un resultado de búsqueda del prompt generator.
    
    **Ejemplo de uso:**
    ```json
    {
      "search_result": {
        "sentencia": "T-040/25",
        "fecha": "2025-02-05",
        "tema": "DERECHO A LA EDUCACIÓN INCLUSIVA DE NIÑOS, NIÑAS Y ADOLESCENTES",
        "sintesis": "En este caso se atribuye la vulneración...",
        "magistrados": ["Jorge Enrique Ibáñez Najar"],
        "expediente": "T-10389113",
        "url_html": "https://www.corteconstitucional.gov.co/relatoria/2025/T-040-25.htm",
        "score": 18.736814,
        "razon_seleccion": "Caso muy relevante sobre derecho a la educación..."
      }
    }
    ```
    
    **Respuesta:**
    ```json
    {
      "document_id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "sentencia_T-040-25.html",
      "url": "https://supabase.url/storage/...",
      "original_url": "https://www.corteconstitucional.gov.co/relatoria/2025/T-040-25.htm",
      "text_length": 45230,
      "text_preview": "SENTENCIA T-040/25...",
      "indexing_result": {
        "chunks_indexed": 23,
        "embedding_model": "text-embedding-3-small"
      },
      "metadata": {
        "sentencia": "T-040/25",
        "fecha": "2025-02-05",
        "tema": "DERECHO A LA EDUCACIÓN INCLUSIVA DE NIÑOS, NIÑAS Y ADOLESCENTES",
        "magistrados": ["Jorge Enrique Ibáñez Najar"],
        "expediente": "T-10389113",
        "score": 18.736814,
        "razon_seleccion": "Caso muy relevante sobre derecho a la educación..."
      }
    }
    ```
    
    - **search_result**: Resultado completo de búsqueda del prompt generator
    """
    try:
        processor = SentenciaProcessor()
        result = await processor.process_sentencia_from_search_result(
            db=db,
            search_result=request.search_result
        )
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando resultado de búsqueda: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Verifica el estado del servicio de procesamiento de sentencias.
    """
    return {
        "status": "healthy",
        "service": "sentencia-processor",
        "message": "Servicio de procesamiento de sentencias operativo"
    }
