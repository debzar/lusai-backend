"""
Rutas para el servicio de búsqueda de sentencias.
"""

from fastapi import APIRouter, HTTPException
from app.services.corte_middleware import CorteMiddleware, SearchRequest

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/sentencias")
async def buscar_sentencias(request: SearchRequest):
    """
    Proxy directo a la API de la Corte Constitucional.
    
    Retorna la respuesta exacta de la API oficial sin modificaciones.
    
    - **fecha_inicio**: Fecha de inicio de búsqueda (formato: YYYY-MM-DD)
    - **fecha_fin**: Fecha de fin de búsqueda (formato: YYYY-MM-DD)  
    - **palabra**: Término de búsqueda
    - **extra**: Términos adicionales (opcional)
    - **pagina**: Número de página (opcional, por defecto 0)
    """
    try:
        middleware = CorteMiddleware()
        response = await middleware.buscar_sentencias(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en proxy: {str(e)}")

