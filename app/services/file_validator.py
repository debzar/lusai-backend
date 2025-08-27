"""
Servicio para validar archivos y detectar inconsistencias entre extensión y contenido real.
"""
import re
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

# Firmas de bytes iniciales (magic numbers) para identificar tipos de archivo
FILE_SIGNATURES = {
    # PDF: inicia con '%PDF'
    "application/pdf": [b'%PDF'],
    
    # DOCX (y otros Office Open XML): inician con PK
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [b'PK'],
    
    # RTF: inicia con {\\rtf
    "application/rtf": [b'{\\rtf', b'{rtf'],
    "text/rtf": [b'{\\rtf', b'{rtf'],
    
    # DOC (MS Word): firmas complejas
    "application/msword": [b'\xD0\xCF\x11\xE0', b'\x00\x01\x00\x00', b'\xFE\x37\x00\x23'],
}

# Mapeo de extensiones de archivo a tipos MIME
EXTENSION_TO_MIME = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "rtf": "application/rtf",
    "doc": "application/msword",
}

# Mapeo de tipos MIME a extensiones (para sugerencias)
MIME_TO_EXTENSION = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/rtf": "rtf",
    "text/rtf": "rtf",
    "application/msword": "doc",
}

def detect_file_type(file_bytes: bytes) -> str:
    """
    Detecta el tipo MIME real de un archivo basado en su contenido binario.
    
    Args:
        file_bytes: Contenido del archivo en bytes
        
    Returns:
        Tipo MIME detectado o None si no se puede determinar
    """
    # Verificamos las firmas de bytes para cada tipo
    for mime_type, signatures in FILE_SIGNATURES.items():
        for signature in signatures:
            if file_bytes.startswith(signature):
                return mime_type
                
    # Algunos casos especiales adicionales
    sample = file_bytes[:20]
    
    # Verificación adicional para DOCX/ZIP
    if b'PK' in sample[:10]:
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
    # Búsqueda más flexible para RTF
    try:
        text_sample = file_bytes[:200].decode('latin1', errors='ignore')
        if '{\\rtf' in text_sample or '\\rtf' in text_sample:
            return "application/rtf"
    except:
        pass
        
    # No pudimos detectar el tipo
    return None

def validate_file_extension(filename: str, content_type: str, file_bytes: bytes) -> Tuple[bool, str, str]:
    """
    Valida que la extensión del archivo coincida con su contenido real.
    
    Args:
        filename: Nombre del archivo incluyendo extensión
        content_type: Tipo MIME declarado por el cliente
        file_bytes: Contenido del archivo en bytes
        
    Returns:
        Tupla con:
        - bool: True si es válido, False si hay inconsistencia
        - str: Mensaje de error o éxito
        - str: Tipo MIME real detectado o None
    """
    # Extraer extensión del nombre del archivo
    extension = ""
    if "." in filename:
        extension = filename.split(".")[-1].lower()
    
    # Detectar tipo real basado en los bytes
    detected_type = detect_file_type(file_bytes)
    logger.debug(f"Archivo: {filename}, Tipo declarado: {content_type}, Tipo detectado: {detected_type}")
    
    # Si no pudimos detectar el tipo, confiamos en el tipo declarado
    if not detected_type:
        logger.warning(f"No se pudo detectar el tipo real del archivo {filename}")
        return True, "No se pudo verificar el formato real del archivo, procediendo con el tipo declarado", content_type
    
    # Verificar consistencia entre extensión y tipo detectado
    expected_extension = MIME_TO_EXTENSION.get(detected_type)
    
    # Si la extensión no coincide con el tipo detectado
    if extension and expected_extension and extension != expected_extension:
        error_msg = (f"La extensión del archivo (.{extension}) no corresponde con su contenido real. "
                    f"El archivo parece ser un {expected_extension.upper()}. "
                    f"Por favor renómbrelo con la extensión .{expected_extension}")
        return False, error_msg, detected_type
        
    # Verificar consistencia entre tipo declarado y tipo detectado
    if content_type != detected_type:
        # Para RTF, permitimos ambas variantes
        if (content_type in ["application/rtf", "text/rtf"] and 
            detected_type in ["application/rtf", "text/rtf"]):
            return True, "Tipo RTF verificado", detected_type
            
        logger.warning(f"Tipo declarado ({content_type}) difiere del detectado ({detected_type})")
        return False, f"El tipo de archivo declarado no coincide con su contenido real. Se detectó: {detected_type}", detected_type
    
    # Todo correcto
    return True, "Validación exitosa", detected_type

def validate_and_fix_filename(filename: str, content_type: str, file_bytes: bytes) -> Tuple[bool, str, str, str]:
    """
    Valida la extensión del archivo y la corrige automáticamente si es necesario.
    
    Args:
        filename: Nombre del archivo incluyendo extensión
        content_type: Tipo MIME declarado por el cliente
        file_bytes: Contenido del archivo en bytes
        
    Returns:
        Tupla con:
        - bool: True si es válido o se pudo corregir
        - str: Mensaje informativo
        - str: Tipo MIME real detectado
        - str: Nombre del archivo corregido (puede ser igual al original)
    """
    # Detectar tipo real basado en los bytes
    detected_type = detect_file_type(file_bytes)
    logger.debug(f"Archivo: {filename}, Tipo declarado: {content_type}, Tipo detectado: {detected_type}")
    
    # Si no pudimos detectar el tipo, usar el original
    if not detected_type:
        logger.warning(f"No se pudo detectar el tipo real del archivo {filename}")
        return True, "No se pudo verificar el formato real del archivo, usando nombre original", content_type, filename
    
    # Obtener la extensión correcta para el tipo detectado
    correct_extension = MIME_TO_EXTENSION.get(detected_type)
    
    if not correct_extension:
        logger.warning(f"No hay extensión conocida para el tipo {detected_type}")
        return True, f"Tipo detectado: {detected_type}, usando nombre original", detected_type, filename
    
    # Extraer extensión actual del archivo
    current_extension = ""
    base_name = filename
    if "." in filename:
        parts = filename.rsplit(".", 1)
        base_name = parts[0]
        current_extension = parts[1].lower()
    
    # Si la extensión actual no coincide con la correcta, corregir
    if current_extension != correct_extension:
        corrected_filename = f"{base_name}.{correct_extension}"
        message = f"Archivo renombrado de '{filename}' a '{corrected_filename}' (tipo real: {correct_extension.upper()})"
        logger.info(message)
        return True, message, detected_type, corrected_filename
    
    # La extensión ya es correcta
    return True, f"Validación exitosa, tipo: {correct_extension.upper()}", detected_type, filename
