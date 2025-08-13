from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Path, Query
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional, Dict, Any
import logging
import traceback

from app.services.supabase_upload import upload_file_to_supabase, delete_file_from_supabase
from app.services.text_extractor import extract_text_from_bytes
from app.services.docs_service import create_document, get_document, list_documents, count_documents
from app.services.file_validator import validate_file_extension
from app.services.index_service import IndexService
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
    # Validar tipo de archivo declarado
    if file.content_type not in ALLOWED_TYPES:
        logger.warning(f"Tipo de archivo no permitido: {file.content_type}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": 400,
                "status": "error",
                "detail": f"Tipo de archivo no permitido. Solo PDF, DOC, DOCX o RTF. Recibido: {file.content_type}"
            }
        )

    # Leer el archivo
    file_bytes = await file.read()

    # Validar tamaño del archivo
    if len(file_bytes) > MAX_FILE_SIZE:
        logger.warning(f"Archivo demasiado grande: {len(file_bytes)} bytes")
        return JSONResponse(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            content={
                "code": 413,
                "status": "error",
                "detail": f"El archivo excede el tamaño máximo permitido de {MAX_FILE_SIZE/1024/1024}MB"
            }
        )

    if len(file_bytes) == 0:
        logger.warning("Archivo vacío")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": 400,
                "status": "error",
                "detail": "El archivo está vacío."
            }
        )

    # Validar que la extensión coincida con el contenido real del archivo
    is_valid, message, detected_type = validate_file_extension(
        filename=file.filename,
        content_type=file.content_type,
        file_bytes=file_bytes
    )

    if not is_valid:
        logger.warning(f"Inconsistencia en extensión/tipo: {message}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": 422,
                "status": "error",
                "detail": message
            }
        )

    # Usar el tipo detectado si está disponible
    effective_content_type = detected_type or file.content_type
    logger.info(f"Tipo de contenido validado: {effective_content_type}")

    public_url = None

    try:
        # Subir archivo a Supabase
        logger.info(f"Intentando subir archivo {file.filename} a Supabase")
        public_url = upload_file_to_supabase(file_bytes, file.filename, effective_content_type)
        logger.info(f"Archivo subido exitosamente a: {public_url}")

        # Extraer texto del documento
        logger.info("Extrayendo texto del documento...")
        extracted_text = extract_text_from_bytes(file_bytes, effective_content_type)
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
                content_type=effective_content_type,
                text_preview=text_preview,
                full_text=extracted_text
            )
            logger.info(f"Documento guardado con ID: {document.id}")
        except Exception as db_error:
            logger.error(f"ERROR AL GUARDAR EN BASE DE DATOS: {str(db_error)}")
            logger.error(traceback.format_exc())
            raise

        # Devolver respuesta con formato estandarizado
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "code": 201,
                "status": "success",
                "data": {
                    "id": str(document.id),
                    "filename": document.filename,
                    "url": document.url,
                    "preview": document.text_preview
                }
            }
        )

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

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "status": "error",
                "detail": f"Error al procesar el archivo: {str(e)}"
            }
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
    try:
        documents = await list_documents(db, limit, offset)
        total = await count_documents(db)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": 200,
                "status": "success",
                "data": {
                    "items": [doc.to_dict() for doc in documents],
                    "total": total,
                    "limit": limit,
                    "offset": offset
                }
            }
        )
    except Exception as e:
        logger.error(f"Error al listar documentos: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "status": "error",
                "detail": f"Error al obtener lista de documentos: {str(e)}"
            }
        )


@router.get("/unindexed", summary="Obtener documentos sin indexar")
async def get_unindexed_documents(
    db: AsyncSession = Depends(get_db)
):
    """
    Obtiene la lista de documentos que no han sido indexados.

    Returns:
        Lista de documentos sin indexar
    """
    try:
        unindexed_docs = await IndexService.get_unindexed_documents(db)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": 200,
                "status": "success",
                "data": {
                    "documents": [doc.to_dict() for doc in unindexed_docs],
                    "count": len(unindexed_docs)
                }
            }
        )

    except Exception as e:
        logger.error(f"Error al obtener documentos sin indexar: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "status": "error",
                "detail": f"Error al obtener documentos sin indexar: {str(e)}"
            }
        )


@router.post("/reindex", summary="Reindexar todos los documentos sin indexar")
async def reindex_all_documents(
    db: AsyncSession = Depends(get_db)
):
    """
    Indexa todos los documentos que no han sido indexados.

    Returns:
        Lista con resultados de indexación para cada documento
    """
    try:
        results = await IndexService.reindex_all_unindexed(db)

        # Contar éxitos y fallos
        successful = len([r for r in results if "error" not in r])
        failed = len([r for r in results if "error" in r])
        total_chunks = sum([r.get("chunks_indexed", 0) for r in results])

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": 200,
                "status": "success",
                "data": {
                    "results": results,
                    "summary": {
                        "total_documents": len(results),
                        "successful": successful,
                        "failed": failed,
                        "total_chunks_created": total_chunks
                    }
                }
            }
        )

    except Exception as e:
        logger.error(f"Error en reindexación masiva: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "status": "error",
                "detail": f"Error en reindexación: {str(e)}"
            }
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
    try:
        document = await get_document(db, document_id)
        if not document:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "code": 404,
                    "status": "error",
                    "detail": f"Documento con ID {document_id} no encontrado"
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": 200,
                "status": "success",
                "data": document.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"Error al obtener documento {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "status": "error",
                "detail": f"Error al obtener documento: {str(e)}"
            }
        )


@router.get("/{document_id}/text", summary="Obtener texto completo")
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
    try:
        document = await get_document(db, document_id)
        if not document:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "code": 404,
                    "status": "error",
                    "detail": f"Documento con ID {document_id} no encontrado"
                }
            )
        
        # Para este endpoint específico mantenemos la respuesta como texto plano
        # ya que es lo que espera el cliente (especificado con response_class=PlainTextResponse)
        if not document.full_text:
            return PlainTextResponse(
                content="",
                status_code=status.HTTP_200_OK
            )
        
        return PlainTextResponse(
            content=document.full_text,
            status_code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error al obtener texto del documento {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "status": "error",
                "detail": f"Error al obtener texto del documento: {str(e)}"
            }
        )


@router.post("/index/{document_id}", summary="Indexar un documento específico")
async def index_document(
    document_id: uuid.UUID = Path(..., description="ID del documento a indexar"),
    db: AsyncSession = Depends(get_db)
):
    """
    Indexa un documento específico generando chunks y embeddings.

    - **document_id**: ID UUID del documento a indexar

    Returns:
        Resultado de la indexación con número de chunks creados
    """
    try:
        result = await IndexService.index_document(db, document_id)
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "code": 200,
                "status": "success",
                "data": result
            }
        )
        
    except ValueError as e:
        logger.warning(f"Error de validación al indexar documento {document_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "code": 400,
                "status": "error",
                "detail": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error al indexar documento {document_id}: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "code": 500,
                "status": "error",
                "detail": f"Error al indexar documento: {str(e)}"
            }
        )

