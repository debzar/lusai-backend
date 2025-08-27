"""
Servicio para procesar sentencias de la Corte Constitucional.
Descarga HTML de sentencias, extrae el texto y las indexa usando la infraestructura existente.
"""

import logging
import requests
import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.docs_service import create_document
from app.services.index_service import IndexService
from app.services.supabase_upload import upload_file_to_supabase

logger = logging.getLogger(__name__)

class SentenciaProcessor:
    """Procesador de sentencias de la Corte Constitucional."""
    
    def __init__(self):
        self.base_url = "https://www.corteconstitucional.gov.co/relatoria/"
    
    async def process_sentencia_from_url(self, db: AsyncSession, sentencia_url: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Procesa una sentencia desde su URL, la descarga, extrae el texto y la indexa.
        
        Args:
            db: Sesión de base de datos
            sentencia_url: URL completa de la sentencia (ej: https://www.corteconstitucional.gov.co/relatoria/2025/T-040-25.htm)
            metadata: Metadatos adicionales de la sentencia (opcional)
            
        Returns:
            Dict con información del procesamiento
        """
        try:
            logger.info(f"🏛️ Procesando sentencia desde URL: {sentencia_url}")
            
            # 1. Descargar HTML de la sentencia
            html_content = await self._download_sentencia_html(sentencia_url)
            
            # 2. Extraer texto del HTML
            extracted_text = self._extract_text_from_html(html_content)
            
            if not extracted_text or len(extracted_text.strip()) < 100:
                raise ValueError("No se pudo extraer texto significativo de la sentencia")
            
            # 3. Generar nombre de archivo basado en la URL
            filename = self._generate_filename_from_url(sentencia_url)
            
            # 4. Subir el texto como archivo a Supabase (para mantener consistencia)
            file_url = await self._upload_text_to_supabase(extracted_text, filename)
            
            # 5. Crear documento en la base de datos
            document = await create_document(
                db=db,
                filename=filename,
                url=file_url,
                content_type="text/html",
                text_preview=extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text,
                full_text=extracted_text
            )
            
            # 6. Indexar el documento automáticamente
            indexing_result = await IndexService.index_document(db, document.id)
            
            logger.info(f"✅ Sentencia procesada exitosamente: {filename}")
            
            return {
                "document_id": str(document.id),
                "filename": filename,
                "url": file_url,
                "original_url": sentencia_url,
                "text_length": len(extracted_text),
                "text_preview": extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text,
                "indexing_result": indexing_result,
                "metadata": metadata or {}
            }
            
        except Exception as e:
            logger.error(f"Error procesando sentencia {sentencia_url}: {e}")
            raise
    
    async def process_sentencia_from_search_result(self, db: AsyncSession, search_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una sentencia desde un resultado de búsqueda del prompt generator.
        
        Args:
            db: Sesión de base de datos
            search_result: Resultado de búsqueda con metadata de la sentencia
            
        Returns:
            Dict con información del procesamiento
        """
        try:
            # Extraer URL del resultado de búsqueda
            sentencia_url = search_result.get('url_html')
            if not sentencia_url:
                raise ValueError("No se encontró URL en el resultado de búsqueda")
            
            # Preparar metadatos de la sentencia
            metadata = {
                "sentencia": search_result.get('sentencia'),
                "fecha": search_result.get('fecha'),
                "tema": search_result.get('tema'),
                "sintesis": search_result.get('sintesis'),
                "magistrados": search_result.get('magistrados', []),
                "expediente": search_result.get('expediente'),
                "score": search_result.get('score'),
                "razon_seleccion": search_result.get('razon_seleccion')
            }
            
            # Procesar la sentencia
            return await self.process_sentencia_from_url(db, sentencia_url, metadata)
            
        except Exception as e:
            logger.error(f"Error procesando resultado de búsqueda: {e}")
            raise
    
    async def _download_sentencia_html(self, url: str) -> str:
        """Descarga el HTML de una sentencia."""
        try:
            logger.info(f"📥 Descargando HTML desde: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Detectar encoding
            response.encoding = response.apparent_encoding or 'utf-8'
            
            logger.info(f"✅ HTML descargado exitosamente ({len(response.text)} caracteres)")
            return response.text
            
        except Exception as e:
            logger.error(f"Error descargando HTML: {e}")
            raise
    
    def _extract_text_from_html(self, html_content: str) -> str:
        """Extrae el texto limpio del HTML de una sentencia."""
        try:
            logger.info("🔍 Extrayendo texto del HTML")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remover scripts, styles y otros elementos no deseados
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                element.decompose()
            
            # Buscar el contenido principal de la sentencia
            # Intentar diferentes selectores comunes para el contenido
            main_content = None
            
            # Intentar selectores comunes para el contenido principal
            selectors = [
                'div.content',
                'div.main-content', 
                'div.document-content',
                'div.sentencia-content',
                'main',
                'article',
                'div.texto',
                'div.contenido'
            ]
            
            for selector in selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    logger.debug(f"Contenido encontrado con selector: {selector}")
                    break
            
            # Si no encontramos un contenedor específico, usar el body completo
            if not main_content:
                main_content = soup.find('body') or soup
                logger.debug("Usando contenido completo del body")
            
            # Extraer texto
            text = main_content.get_text(separator='\n', strip=True)
            
            # Limpiar el texto
            text = self._clean_extracted_text(text)
            
            logger.info(f"✅ Texto extraído ({len(text)} caracteres)")
            return text
            
        except Exception as e:
            logger.error(f"Error extrayendo texto del HTML: {e}")
            raise
    
    def _clean_extracted_text(self, text: str) -> str:
        """Limpia y normaliza el texto extraído."""
        if not text:
            return ""
        
        # Normalizar espacios en blanco y saltos de línea
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalizar párrafos
        text = re.sub(r'\t+', ' ', text)  # Reemplazar tabs con espacios
        text = re.sub(r' +', ' ', text)  # Normalizar espacios múltiples
        
        # Remover líneas muy cortas que probablemente sean ruido
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Mantener líneas con contenido significativo
            if len(line) > 3 or re.match(r'^\d+\.?\s*$', line):  # Números de sección
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Remover caracteres de control problemáticos
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()
    
    def _generate_filename_from_url(self, url: str) -> str:
        """Genera un nombre de archivo basado en la URL de la sentencia."""
        # Extraer el nombre del archivo de la URL
        # Ej: https://www.corteconstitucional.gov.co/relatoria/2025/T-040-25.htm -> T-040-25.htm
        filename = url.split('/')[-1]
        
        # Si no tiene extensión, agregar .html
        if '.' not in filename:
            filename += '.html'
        
        # Cambiar .htm a .html para consistencia
        if filename.endswith('.htm'):
            filename = filename[:-4] + '.html'
        
        # Agregar prefijo para identificar que es una sentencia
        if not filename.startswith('sentencia_'):
            filename = f"sentencia_{filename}"
        
        return filename
    
    async def _upload_text_to_supabase(self, text: str, filename: str) -> str:
        """Sube el texto extraído a Supabase como archivo."""
        try:
            # Convertir texto a bytes
            text_bytes = text.encode('utf-8')
            
            # Usar el servicio de Supabase existente
            file_url = upload_file_to_supabase(
                file_bytes=text_bytes,
                filename=filename,
                content_type="text/html"
            )
            
            logger.info(f"📤 Texto subido a Supabase: {file_url}")
            return file_url
            
        except Exception as e:
            logger.error(f"Error subiendo texto a Supabase: {e}")
            # Fallback: retornar URL original si falla la subida
            return f"local://text/{filename}"
