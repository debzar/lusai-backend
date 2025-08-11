"""
Servicio para indexar documentos con embeddings de OpenAI.
Divide documentos en chunks y genera embeddings para búsqueda vectorial.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
import asyncio
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.models.document import Document
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)

# Configuración de OpenAI
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Configuración de chunks
MAX_CHUNK_CHARS = 2000  # Aproximadamente 500 tokens
CHUNK_OVERLAP = 200     # Superposición entre chunks

class IndexService:
    """Servicio para indexar documentos con embeddings vectoriales"""
    
    @staticmethod
    def _split_text_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """
        Divide el texto en chunks con superposición.
        
        Args:
            text: Texto a dividir
            max_chars: Máximo de caracteres por chunk
            overlap: Caracteres de superposición entre chunks
            
        Returns:
            Lista de chunks de texto
        """
        if not text or len(text) <= max_chars:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_chars
            
            # Si no es el último chunk, buscar un punto de corte natural
            if end < len(text):
                # Buscar el último punto, nueva línea o espacio antes del límite
                for delimiter in ['\n\n', '\n', '. ', ' ']:
                    last_delim = text.rfind(delimiter, start, end)
                    if last_delim != -1:
                        end = last_delim + len(delimiter)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Mover el inicio considerando la superposición
            start = max(start + 1, end - overlap)
            
            # Evitar bucle infinito
            if start >= len(text):
                break
        
        return chunks
    
    @staticmethod
    async def _generate_embedding(text: str) -> List[float]:
        """
        Genera embedding usando OpenAI text-embedding-ada-002.
        
        Args:
            text: Texto para generar embedding
            
        Returns:
            Vector de embedding
            
        Raises:
            Exception: Si falla la generación del embedding
        """
        try:
            response = await client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise Exception(f"Error al generar embedding: {str(e)}")
    
    @staticmethod
    async def index_document(db: AsyncSession, document_id: UUID) -> Dict[str, Any]:
        """
        Indexa un documento dividiéndolo en chunks y generando embeddings.
        
        Args:
            db: Sesión de base de datos
            document_id: ID del documento a indexar
            
        Returns:
            Diccionario con información de la indexación
            
        Raises:
            ValueError: Si el documento no existe o no tiene texto
            Exception: Si falla la indexación
        """
        try:
            # Buscar el documento
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            
            if not document:
                raise ValueError(f"Documento con ID {document_id} no encontrado")
            
            if not document.full_text:
                raise ValueError(f"El documento {document_id} no tiene texto para indexar")
            
            # Verificar si ya tiene chunks (limpiar si existen)
            existing_chunks = await db.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            existing_chunks_list = existing_chunks.scalars().all()
            
            if existing_chunks_list:
                logger.info(f"Eliminando {len(existing_chunks_list)} chunks existentes para documento {document_id}")
                for chunk in existing_chunks_list:
                    await db.delete(chunk)
                await db.flush()
            
            # Dividir texto en chunks
            chunks = IndexService._split_text_into_chunks(document.full_text)
            
            if not chunks:
                raise ValueError(f"No se pudieron generar chunks para el documento {document_id}")
            
            logger.info(f"Generando {len(chunks)} chunks para documento {document_id}")
            
            # Procesar chunks y generar embeddings
            chunks_created = 0
            
            for i, chunk_text in enumerate(chunks):
                try:
                    # Generar embedding
                    embedding_vector = await IndexService._generate_embedding(chunk_text)
                    
                    # Crear chunk en la base de datos
                    # Convertir el vector a JSON string para almacenamiento
                    embedding_json = json.dumps(embedding_vector)
                    
                    # Usar SQL raw para insertar con vector pgvector
                    await db.execute(
                        text("""
                            INSERT INTO document_chunks (document_id, chunk_text, embedding)
                            VALUES (:document_id, :chunk_text, :embedding::vector)
                        """),
                        {
                            "document_id": str(document_id),
                            "chunk_text": chunk_text,
                            "embedding": f"[{','.join(map(str, embedding_vector))}]"
                        }
                    )
                    
                    chunks_created += 1
                    logger.debug(f"Chunk {i+1}/{len(chunks)} indexado para documento {document_id}")
                    
                    # Pequeña pausa para evitar rate limiting de OpenAI
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error procesando chunk {i+1} del documento {document_id}: {e}")
                    # Continuar con el siguiente chunk
                    continue
            
            await db.commit()
            
            logger.info(f"Indexación completada para documento {document_id}: {chunks_created} chunks creados")
            
            return {
                "document_id": str(document_id),
                "chunks_indexed": chunks_created,
                "total_chunks": len(chunks)
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error indexando documento {document_id}: {e}")
            raise
    
    @staticmethod
    async def get_unindexed_documents(db: AsyncSession) -> List[Document]:
        """
        Obtiene documentos que no han sido indexados.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Lista de documentos sin indexar
        """
        try:
            # Buscar documentos que tienen full_text pero no tienen chunks
            result = await db.execute(
                select(Document).where(
                    Document.full_text.isnot(None),
                    Document.full_text != "",
                    ~Document.id.in_(
                        select(DocumentChunk.document_id).distinct()
                    )
                )
            )
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error obteniendo documentos sin indexar: {e}")
            raise
    
    @staticmethod
    async def reindex_all_unindexed(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Indexa todos los documentos que no han sido indexados.
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            Lista con resultados de indexación
        """
        try:
            unindexed_docs = await IndexService.get_unindexed_documents(db)
            
            if not unindexed_docs:
                logger.info("No hay documentos pendientes de indexar")
                return []
            
            logger.info(f"Indexando {len(unindexed_docs)} documentos")
            
            results = []
            
            for doc in unindexed_docs:
                try:
                    result = await IndexService.index_document(db, doc.id)
                    results.append(result)
                    logger.info(f"Documento {doc.filename} indexado exitosamente")
                    
                except Exception as e:
                    logger.error(f"Error indexando documento {doc.filename}: {e}")
                    results.append({
                        "document_id": str(doc.id),
                        "chunks_indexed": 0,
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error en reindexación masiva: {e}")
            raise
