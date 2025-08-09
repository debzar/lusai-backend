from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Path, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional
import logging
import traceback

from app.services.supabase_upload import upload_file_to_supabase, delete_file_from_supabase
from app.services.text_extractor import extract_text_from_bytes
from app.services.docs_service import create_document, get_document, list_documents, count_documents
from app.db.database import get_db
from app.models.document import Document

# Configurar logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

router = APIRouter()

# Tipos MIME permitidos
ALLOWED_TYPES = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/rtf": ".rtf",
    "text/rtf": ".rtf"
}

# Tamaño máximo de archivo en bytes (20MB)
MAX_FILE_SIZE = 20 * 1024 * 1024

@router.post("/upload_file", status_code=201, summary="Subir un documento")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Sube un documento, extrae el texto y almacena la metadata.

    - **file**: El archivo a subir (PDF, DOC, DOCX o RTF)

    Returns:
        Un objeto JSON con id, filename, url y preview del texto extraído
    """
    # Validar tipo de archivo
    if file.content_type not in ALLOWED_TYPES:
        logger.warning(f"Tipo de archivo no permitido: {file.content_type}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Solo PDF, DOC, DOCX o RTF. Recibido: {file.content_type}"
        )

    # Leer el archivo
    file_bytes = await file.read()

    # Validar tamaño del archivo
    if len(file_bytes) > MAX_FILE_SIZE:
        logger.warning(f"Archivo demasiado grande: {len(file_bytes)} bytes")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE/1024/1024}MB"
        )

    if len(file_bytes) == 0:
        logger.warning("Archivo vacío")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío."
        )

    public_url = None

    try:
        # Subir archivo a Supabase
        logger.info(f"Intentando subir archivo {file.filename} a Supabase")
        public_url = upload_file_to_supabase(file_bytes, file.filename, file.content_type)
        logger.info(f"Archivo subido exitosamente a: {public_url}")

        # Extraer texto del documento
        logger.info("Extrayendo texto del documento...")
        extracted_text = extract_text_from_bytes(file_bytes, file.content_type)
        logger.debug(f"Texto extraído (primeros 100 caracteres): {extracted_text[:100] if extracted_text else None}")

        # Crear vista previa (primeros 1000 caracteres)
        text_preview = extracted_text[:1000] if extracted_text else None

        # Guardar metadata en la base de datos
        logger.info("Guardando metadata en base de datos...")
        try:
            document = await create_document(
                db=db,
                filename=file.filename,
                url=public_url,
                content_type=file.content_type,
                text_preview=text_preview,
                full_text=extracted_text
            )
            logger.info(f"Documento guardado con ID: {document.id}")
        except Exception as db_error:
            logger.error(f"ERROR AL GUARDAR EN BASE DE DATOS: {str(db_error)}")
            logger.error(traceback.format_exc())
            raise

        # Devolver respuesta
        return {
            "id": str(document.id),
            "filename": document.filename,
            "url": document.url,
            "preview": document.text_preview
        }

    except Exception as e:
        # Log detallado del error
        logger.error(f"ERROR EN PROCESO DE SUBIDA: {str(e)}")
        logger.error(traceback.format_exc())

        # Si hay error y el archivo ya se subió, eliminar
        if public_url:
            logger.info(f"Intentando eliminar archivo subido: {public_url}")
            try:
                # Extraer path del public_url para eliminación
                path = public_url.split('/')[-1]
                deleted = delete_file_from_supabase(path)
                logger.info(f"Archivo eliminado: {deleted}")
            except Exception as delete_error:
                # Log error pero continuar con la respuesta de error original
                logger.error(f"Error al eliminar archivo: {str(delete_error)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el archivo: {str(e)}"
        )

# ¡IMPORTANTE! Colocar la ruta /documents ANTES que la ruta /{document_id}
# para evitar conflictos en la resolución de rutas
@router.get("/documents", summary="Listar documentos")
async def list_documents_endpoint(
    limit: int = Query(10, ge=1, le=100, description="Número máximo de documentos"),
    offset: int = Query(0, ge=0, description="Número de documentos a saltar"),
    db: AsyncSession = Depends(get_db)
):
    """
    Lista documentos con paginación.

    - **limit**: Número máximo de documentos a devolver (1-100)
    - **offset**: Número de documentos a saltar para la paginación

    Returns:
        Lista de documentos y metadata de paginación
    """
    documents = await list_documents(db, limit, offset)
    total = await count_documents(db)

    return {
        "items": [doc.to_dict() for doc in documents],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{document_id}", summary="Obtener metadata de un documento")
async def get_document_by_id(
    document_id: uuid.UUID = Path(..., description="ID del documento"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene la metadata de un documento por su ID.

    - **document_id**: ID UUID del documento

    Returns:
        Metadata del documento (id, filename, url, preview, created_at)
    """
    document = await get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} no encontrado"
        )

    return document.to_dict()


@router.get("/{document_id}/text", response_class=PlainTextResponse, summary="Obtener texto completo")
async def get_document_text(
    document_id: uuid.UUID = Path(..., description="ID del documento"),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene el texto completo extraído de un documento.

    - **document_id**: ID UUID del documento

    Returns:
        Texto plano completo extraído del documento
    """
    document = await get_document(db, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Documento con ID {document_id} no encontrado"
        )

    if not document.full_text:
        return ""

    return document.full_text
