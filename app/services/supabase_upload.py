import os
from supabase import create_client, Client
from dotenv import load_dotenv
from typing import Optional
import uuid

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
