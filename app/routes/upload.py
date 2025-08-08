from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Path, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

from app.services.supabase_upload import upload_file_to_supabase, delete_file_from_supabase
from app.services.text_extractor import extract_text_from_bytes
from app.services.docs_service import create_document, get_document, list_documents, count_documents
from app.db.database import get_db
from app.models.document import Document

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no permitido. Solo PDF, DOC, DOCX o RTF. Recibido: {file.content_type}"
        )

    # Leer el archivo
    file_bytes = await file.read()

    # Validar tamaño del archivo
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE/1024/1024}MB"
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío."
        )

    public_url = None

    try:
        # Subir archivo a Supabase
        public_url = upload_file_to_supabase(file_bytes, file.filename, file.content_type)

        # Extraer texto del documento
        extracted_text = extract_text_from_bytes(file_bytes, file.content_type)

        # Crear vista previa (primeros 1000 caracteres)
        text_preview = extracted_text[:1000] if extracted_text else None

        # Guardar metadata en la base de datos
        document = await create_document(
            db=db,
            filename=file.filename,
            url=public_url,
            content_type=file.content_type,
            text_preview=text_preview,
            full_text=extracted_text
        )

        # Devolver respuesta
        return {
            "id": str(document.id),
            "filename": document.filename,
            "url": document.url,
            "preview": document.text_preview
        }

    except Exception as e:
        # Si hay error y el archivo ya se subió, eliminar
        if public_url:
            try:
                # Extraer path del public_url para eliminación
                path = public_url.split('/')[-1]
                delete_file_from_supabase(path)
            except Exception as delete_error:
                # Log error pero continuar con la respuesta de error original
                print(f"Error al eliminar archivo: {delete_error}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el archivo: {str(e)}"
        )


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
