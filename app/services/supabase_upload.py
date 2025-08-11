import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional
import uuid
import logging
import re

logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()  # Eliminar espacios o caracteres adicionales
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "sentencias")

# Verificar si hay un '=' al inicio del token y eliminarlo
if SUPABASE_KEY and SUPABASE_KEY.startswith("="):
    SUPABASE_KEY = SUPABASE_KEY[1:]
    logger.warning("Se eliminó un carácter '=' al inicio del SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_BUCKET:
    raise ValueError("Faltan variables de entorno para Supabase.")

# Intentar crear el cliente con el token limpio
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Cliente Supabase creado exitosamente")
except Exception as e:
    logger.error(f"Error al crear cliente Supabase: {str(e)}")
    raise

def upload_file_to_supabase(file_bytes: bytes, filename: Optional[str] = None, content_type: Optional[str] = None) -> str:
    """
    Sube un archivo a Supabase Storage y retorna la URL pública.

    Args:
        file_bytes: Contenido del archivo en bytes
        filename: Nombre original del archivo
        content_type: Tipo MIME del archivo

    Returns:
        URL pública del archivo en Supabase Storage

    Raises:
        Exception: Si hay un error en la subida
    """
    if not filename:
        filename = f"{uuid.uuid4()}"
    
    # Sanitizar nombre de archivo para evitar problemas
    # Eliminar caracteres especiales y espacios
    safe_filename = re.sub(r'[^\w\.-]', '_', filename)
    
    # Guardar en subcarpeta según extensión
    ext = safe_filename.split('.')[-1].lower() if '.' in safe_filename else 'bin'
    path = f"uploads/{safe_filename}"
    
    logger.debug(f"Iniciando subida a bucket '{SUPABASE_BUCKET}', path: '{path}'")
    
    try:
        # Subir archivo con manejo de errores mejorado
        res = supabase.storage.from_(SUPABASE_BUCKET).upload(
            path, 
            file_bytes, 
            file_options={
                "content-type": content_type or "application/octet-stream",
                "x-upsert": "true"  # Sobrescribir si existe
            }
        )
        
        if isinstance(res, dict) and res.get("error"):
            raise Exception(f"Error en respuesta de Supabase: {res['error']['message']}")
        
        # Obtener URL pública
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(path)
        logger.info(f"Archivo subido exitosamente: {public_url}")
        return public_url
        
    except Exception as e:
        logger.error(f"Error durante la subida a Supabase: {str(e)}")
        raise Exception(f"Error al subir archivo a Supabase: {str(e)}")

def delete_file_from_supabase(path: str) -> bool:
    """
    Elimina un archivo de Supabase Storage por su path.
    
    Args:
        path: Ruta del archivo en el bucket
        
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    try:
        # Si el path es una URL completa, extraer sólo la parte final
        if path.startswith('http'):
            parts = path.split('/')
            filename = parts[-1]
            path = f"uploads/{filename}"
        
        logger.debug(f"Intentando eliminar archivo: {path}")
        
        # Eliminar archivo
        res = supabase.storage.from_(SUPABASE_BUCKET).remove([path])
        
        if isinstance(res, dict) and res.get("error"):
            logger.error(f"Error al eliminar archivo: {res['error']['message']}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error eliminando archivo de Supabase: {str(e)}")
        return False
