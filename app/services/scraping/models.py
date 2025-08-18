"""
Modelos de datos para el servicio de scraping.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class SearchRequest(BaseModel):
    """Modelo para solicitudes de búsqueda."""
    fecha_inicio: str = Field(..., description="Fecha de inicio en formato YYYY-MM-DD")
    fecha_fin: str = Field(..., description="Fecha de fin en formato YYYY-MM-DD")
    palabra: str = Field(..., description="Palabra clave a buscar")
    extra: str = Field("", description="Parámetros extra para la búsqueda")
    pagina: int = Field(0, description="Número de página de resultados", ge=0)

class Sentencia(BaseModel):
    """Modelo para una sentencia individual."""
    titulo: str = Field(..., description="Número de la sentencia (ej: T-606/15)")
    url_html: str = Field("", description="Enlace a la sentencia en HTML")
    url_pdf: str = Field("", description="Enlace al PDF de la sentencia")

class SearchResult(BaseModel):
    """Modelo para resultados de búsqueda."""
    tema: str = Field(..., description="Clasificación temática de la sentencia")
    subtema: str = Field("", description="Descripción más específica del tema")
    providencias: List[Sentencia] = Field(default_factory=list, description="Lista de sentencias encontradas")

class ScrapingResponse(BaseModel):
    """Modelo para la respuesta del servicio de scraping."""
    status: str = Field("success", description="Estado de la operación")
    total_resultados: int = Field(0, description="Total de resultados encontrados")
    resultados: List[SearchResult] = Field(default_factory=list, description="Lista de resultados")
    nota: Optional[str] = Field(None, description="Nota adicional sobre los resultados")
