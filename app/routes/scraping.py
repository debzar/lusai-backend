from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from app.services.scraping_service import buscar_sentencias_async
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraping", tags=["scraping"])

from pydantic import BaseModel

class BusquedaSentenciasRequest(BaseModel):
    fecha_inicio: str
    fecha_fin: str
    palabra: str
    extra: str = ""
    pagina: int = 0

@router.post("/sentencias")
async def buscar_sentencias(request: BusquedaSentenciasRequest):
    """Endpoint POST para búsqueda de sentencias."""
    return await _buscar_sentencias_internal(
        request.fecha_inicio, 
        request.fecha_fin, 
        request.palabra, 
        request.extra, 
        request.pagina
    )

async def _buscar_sentencias_internal(
    fecha_inicio: str,
    fecha_fin: str,
    palabra: str,
    extra: str = "",
    pagina: int = 0
):
    """
    Función interna para buscar sentencias en la Corte Constitucional de Colombia.
    
    Retorna una lista de resultados con la siguiente estructura:
    - tema: Clasificación temática de la sentencia
    - subtema: Descripción más específica del tema
    - providencias: Lista de sentencias encontradas, cada una con:
      - titulo: Número de la sentencia (ej: T-606/15)
      - url_html: Enlace a la sentencia en HTML
      - url_pdf: Enlace al PDF (si está disponible)
    """
    try:
        # Validar fechas
        try:
            datetime.strptime(fecha_inicio, "%Y-%m-%d")
            datetime.strptime(fecha_fin, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Las fechas deben estar en formato YYYY-MM-DD"
            )
        
        # Validar que fecha_inicio sea menor que fecha_fin
        if fecha_inicio > fecha_fin:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio debe ser menor que la fecha de fin"
            )
        
        # Validar palabra clave
        if len(palabra.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="La palabra clave debe tener al menos 2 caracteres"
            )
        
        logger.info(f"Buscando sentencias: {fecha_inicio} a {fecha_fin}, palabra: '{palabra}', página: {pagina}")
        
        # Realizar búsqueda
        resultados = await buscar_sentencias_async(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            palabra=palabra,
            extra=extra,
            pagina=pagina
        )
        
        logger.info(f"Búsqueda completada. Encontrados {len(resultados)} resultados")
        
        return {
            "status": "success",
            "total_resultados": len(resultados),
            "parametros": {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "palabra": palabra,
                "extra": extra,
                "pagina": pagina
            },
            "resultados": resultados,
            "nota": "Este servicio combina scraping web con resultados de ejemplo debido a las limitaciones de contenido dinámico de la página de la Corte Constitucional"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en búsqueda de sentencias: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )



@router.post("/buscar-avanzado")
async def buscar_avanzado(request: BusquedaSentenciasRequest):
    """
    Endpoint POST avanzado para búsquedas complejas de sentencias.
    Ideal para búsquedas con texto largo o múltiples parámetros.
    
    Ejemplo de uso:
    {
        "fecha_inicio": "1992-01-01",
        "fecha_fin": "2025-08-17",
        "palabra": "Marcela como agente oficiosa de su nieta Sara en contra de la Secretaría de Educación",
        "extra": "",
        "pagina": 0
    }
    """
    try:
        # Validar fechas
        try:
            datetime.strptime(request.fecha_inicio, "%Y-%m-%d")
            datetime.strptime(request.fecha_fin, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Las fechas deben estar en formato YYYY-MM-DD"
            )
        
        # Validar que fecha_inicio sea menor que fecha_fin
        if request.fecha_inicio > request.fecha_fin:
            raise HTTPException(
                status_code=400,
                detail="La fecha de inicio debe ser menor que la fecha de fin"
            )
        
        # Validar palabra clave
        if len(request.palabra.strip()) < 2:
            raise HTTPException(
                status_code=400,
                detail="La palabra clave debe tener al menos 2 caracteres"
            )
        
        logger.info(f"Búsqueda avanzada: {request.fecha_inicio} a {request.fecha_fin}, palabra: '{request.palabra}', página: {request.pagina}")
        
        # Realizar búsqueda
        resultados = await buscar_sentencias_async(
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            palabra=request.palabra,
            extra=request.extra,
            pagina=request.pagina
        )
        
        logger.info(f"Búsqueda avanzada completada. Encontrados {len(resultados)} resultados")
        
        return {
            "status": "success",
            "metodo": "POST avanzado",
            "total_resultados": len(resultados),
            "parametros": {
                "fecha_inicio": request.fecha_inicio,
                "fecha_fin": request.fecha_fin,
                "palabra": request.palabra,
                "extra": request.extra,
                "pagina": request.pagina
            },
            "resultados": resultados,
            "nota": "Este endpoint POST es ideal para búsquedas con texto largo o múltiples parámetros"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en búsqueda avanzada: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error interno del servidor: {str(e)}"
        )

@router.get("/ejemplos-busqueda")
async def ejemplos_busqueda():
    """
    Devuelve ejemplos de búsquedas que funcionan bien.
    """
    return {
        "status": "success",
        "ejemplos": [
            {
                "descripcion": "Búsqueda principal de sentencias (POST)",
                "url": "/scraping/sentencias",
                "palabra": "educación",
                "metodo": "POST",
                "body_example": {
                    "fecha_inicio": "2020-01-01",
                    "fecha_fin": "2025-08-17",
                    "palabra": "educación",
                    "extra": "",
                    "pagina": 0
                }
            },
            {
                "descripcion": "Búsqueda por derecho específico (POST)",
                "url": "/scraping/sentencias",
                "palabra": "tutela",
                "metodo": "POST",
                "body_example": {
                    "fecha_inicio": "2020-01-01",
                    "fecha_fin": "2025-08-17",
                    "palabra": "tutela",
                    "extra": "",
                    "pagina": 0
                }
            },

            {
                "descripcion": "Búsqueda avanzada con texto largo (POST)",
                "url": "/scraping/buscar-avanzado",
                "palabra": "Marcela como agente oficiosa de su nieta Sara en contra de la Secretaría de Educación",
                "metodo": "POST",
                "body_example": {
                    "fecha_inicio": "1992-01-01",
                    "fecha_fin": "2025-08-17",
                    "palabra": "Marcela como agente oficiosa de su nieta Sara en contra de la Secretaría de Educación",
                    "extra": "",
                    "pagina": 0
                }
            }
        ],
        "consejos": [
            "Para búsquedas específicas, usa palabras clave principales",
            "Las búsquedas muy largas pueden no devolver resultados",
            "Prueba con términos jurídicos comunes como 'tutela', 'constitucionalidad'",
            "El servicio incluye resultados de ejemplo cuando no encuentra datos reales",
            "Para búsquedas con texto largo, usa el endpoint POST /scraping/buscar-avanzado",
            "Todos los endpoints principales usan POST para mejor manejo de parámetros complejos"
        ]
    }

@router.get("/test-conexion")
async def test_conexion_corte():
    """
    Endpoint de prueba para verificar la conectividad con la página de la Corte Constitucional.
    """
    try:
        import requests
        
        url = "https://www.corteconstitucional.gov.co"
        response = requests.get(url, timeout=10)
        
        return {
            "status": "success",
            "url": url,
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "tamaño_contenido": len(response.content)
        }
        
    except Exception as e:
        logger.error(f"Error probando conexión: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error de conectividad: {str(e)}"
        )
