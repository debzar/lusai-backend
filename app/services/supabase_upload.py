import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional
import uuid
import logging

logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_BUCKET:
    raise ValueError("Faltan variables de entorno para Supabase.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
    # Guardar en subcarpeta según extensión
    ext = filename.split('.')[-1].lower() if '.' in filename else 'bin'
    path = f"uploads/{filename}"
    # Subir archivo
    res = supabase.storage.from_(SUPABASE_BUCKET).upload(path, file_bytes, file_options={"content-type": content_type or "application/octet-stream"})
    if res.get("error"):
        raise Exception(f"Error al subir archivo a Supabase: {res['error']['message']}")
    # Obtener URL pública
    public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(path)
    return public_url

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
            # Obtener último segmento de la URL
            file_path = path.split('/')[-2] + '/' + path.split('/')[-1]
        else:
            file_path = path

        # Eliminar archivo
        res = supabase.storage.from_(SUPABASE_BUCKET).remove([file_path])
        if res.get("error"):
            logger.error(f"Error al eliminar archivo de Supabase: {res['error']['message']}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error eliminando archivo de Supabase: {str(e)}")
        return False
