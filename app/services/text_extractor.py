"""
Servicio para extraer texto de diferentes tipos de documentos:
- PDF: utilizando pdfplumber
- DOCX: utilizando python-docx
- DOC: debe ser convertido primero (no soportado directamente)
- RTF: utilizando striprtf
"""
import io
import logging
from typing import Optional

import pdfplumber
from docx import Document
from striprtf.striprtf import rtf_to_text

logger = logging.getLogger(__name__)


def extract_text_from_bytes(file_bytes: bytes, content_type: str) -> Optional[str]:
    """
    Extrae texto plano de archivos en diferentes formatos.
    
    Args:
        file_bytes: Bytes del archivo
        content_type: Tipo MIME del archivo (ej. 'application/pdf')
    
    Returns:
        String con el texto extraído o None si hubo un error
    """
    try:
        if content_type == "application/pdf":
            return extract_from_pdf(file_bytes)
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            return extract_from_docx(file_bytes)
        elif content_type in ["application/rtf", "text/rtf"]:
            return extract_from_rtf(file_bytes)
        elif content_type == "application/msword":
            logger.warning("Extracción directa de archivos .doc no soportada")
            return "El formato DOC requiere conversión previa"
        else:
            logger.error(f"Tipo de documento no soportado: {content_type}")
            return None
    except Exception as e:
        logger.error(f"Error extrayendo texto: {str(e)}")
        return None


def extract_from_pdf(pdf_bytes: bytes) -> str:
    """Extrae texto de un archivo PDF"""
    text_content = []
    
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            text_content.append(text)
    
    return "\n\n".join(text_content)


def extract_from_docx(docx_bytes: bytes) -> str:
    """Extrae texto de un archivo DOCX"""
    doc = Document(io.BytesIO(docx_bytes))
    
    # Extrae el texto de cada párrafo
    text_content = []
    for paragraph in doc.paragraphs:
        if paragraph.text:
            text_content.append(paragraph.text)
    
    # También extrae texto de tablas
    for table in doc.tables:
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                if cell.text:
                    row_text.append(cell.text.strip())
            if row_text:
                text_content.append(" | ".join(row_text))
    
    return "\n\n".join(text_content)


def extract_from_rtf(rtf_bytes: bytes) -> str:
    """Extrae texto de un archivo RTF"""
    # Convertir bytes a string probando diferentes codificaciones
    # para manejar correctamente tildes, ñ y otros caracteres especiales
    encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']

    rtf_text = None
    for encoding in encodings:
        try:
            rtf_text = rtf_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if rtf_text is None:
        return "Error decodificando archivo RTF: no se pudo determinar la codificación"

    # Usar striprtf para convertir RTF a texto plano
    plain_text = rtf_to_text(rtf_text)
    return plain_text
