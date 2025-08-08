"""
Servicio para operaciones CRUD de documentos en la base de datos.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import UUID
from typing import List, Optional
import uuid
import logging

from app.models.document import Document

logger = logging.getLogger(__name__)

async def create_document(
    db: AsyncSession,
    filename: str,
    url: str,
    content_type: str,
    text_preview: Optional[str] = None,
    full_text: Optional[str] = None
) -> Document:
    """
    Crea un nuevo documento en la base de datos.
    
    Args:
        db: Sesión de base de datos
        filename: Nombre original del archivo
        url: URL pública del archivo en Supabase Storage
        content_type: Tipo MIME del archivo
        text_preview: Vista previa del texto extraído (primeros 1000 caracteres)
        full_text: Texto completo extraído del documento
        
    Returns:
        El objeto Document creado
    """
    try:
        document = Document(
            filename=filename,
            url=url,
            content_type=content_type,
            text_preview=text_preview,
            full_text=full_text
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        
        return document
    except Exception as e:
        await db.rollback()
        logger.error(f"Error al crear documento: {str(e)}")
        raise


async def get_document(db: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
    """
    Obtiene un documento por su ID.
    
    Args:
        db: Sesión de base de datos
        document_id: ID del documento
        
    Returns:
        Objeto Document o None si no se encuentra
    """
    try:
        query = select(Document).where(Document.id == document_id)
        result = await db.execute(query)
        document = result.scalars().first()
        return document
    except Exception as e:
        logger.error(f"Error al obtener documento {document_id}: {str(e)}")
        raise


async def list_documents(db: AsyncSession, limit: int = 10, offset: int = 0) -> List[Document]:
    """
    Lista documentos con paginación.
    
    Args:
        db: Sesión de base de datos
        limit: Número máximo de documentos a devolver
        offset: Número de documentos a saltar
        
    Returns:
        Lista de objetos Document
    """
    try:
        query = select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        documents = result.scalars().all()
        return list(documents)
    except Exception as e:
        logger.error(f"Error al listar documentos: {str(e)}")
        raise


async def count_documents(db: AsyncSession) -> int:
    """
    Cuenta el número total de documentos en la base de datos.
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Número total de documentos
    """
    try:
        query = select(Document)
        result = await db.execute(query)
        return len(result.scalars().all())
    except Exception as e:
        logger.error(f"Error al contar documentos: {str(e)}")
        raise
