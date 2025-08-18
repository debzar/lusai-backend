"""
Servicio para indexar documentos con embeddings.
"""
import os
import json
import logging
from typing import List, Dict, Any
from uuid import UUID
import asyncio
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models.document import Document
from app.models.document_chunk import DocumentChunk

logger = logging.getLogger(__name__)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_CHUNK_CHARS = 2000
CHUNK_OVERLAP = 200

# Configuración para selección automática de modelo de embedding
SMALL_DOCUMENT_THRESHOLD = 50000   # ~20 páginas
LARGE_DOCUMENT_THRESHOLD = 150000  # ~60 páginas

class IndexService:

    @staticmethod
    def _get_embedding_model(text_length: int) -> str:
        """
        Selecciona el modelo de embedding más apropiado basado en el tamaño del documento.
        
        Args:
            text_length: Longitud del texto en caracteres
            
        Returns:
            str: Nombre del modelo de embedding a usar
        """
        if text_length <= LARGE_DOCUMENT_THRESHOLD:
            return "text-embedding-3-small"  # Rápido y económico para docs típicos
        else:
            return "text-embedding-3-large"  # Máxima precisión para docs complejos

    @staticmethod
    def _split_text_into_chunks(text: str, max_chars: int = MAX_CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> List[str]:
        if not text or len(text) <= max_chars:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_chars
            
            if end < len(text):
                for delimiter in ['\n\n', '\n', '. ', ' ']:
                    last_delim = text.rfind(delimiter, start, end)
                    if last_delim != -1:
                        end = last_delim + len(delimiter)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + 1, end - overlap)
            
            if start >= len(text):
                break
        
        return chunks
    
    @staticmethod
    async def _generate_embedding(text: str, document_length: int = None) -> List[float]:
        try:
            clean_text = text.encode('utf-8', errors='ignore').decode('utf-8').strip()

            if not clean_text:
                raise ValueError("Texto vacío después de limpieza")

            # Seleccionar modelo basado en el tamaño del documento completo
            model = IndexService._get_embedding_model(document_length or len(clean_text))
            logger.info(f"Usando modelo {model} para documento de {document_length or len(clean_text)} caracteres")

            # ========================================
            # TODO: CAMBIAR A OPENAI CUANDO TENGAS API KEY
            # ========================================
            # PASO 1: Comenta o elimina el código de embedding simulado (líneas de abajo)
            # PASO 2: Descomenta el código real de OpenAI (al final de esta función)
            # PASO 3: Agrega tu OPENAI_API_KEY real al archivo .env
            # ========================================

            # CÓDIGO TEMPORAL: Embedding simulado (ELIMINAR CUANDO USES OPENAI)
            import random
            import hashlib

            seed = int(hashlib.md5(clean_text.encode()).hexdigest()[:8], 16)
            random.seed(seed)
            
            # Ajustar dimensiones según el modelo
            dimensions = 3072 if model == "text-embedding-3-large" else 1536
            embedding_vector = [random.uniform(-1, 1) for _ in range(dimensions)]

            logger.info(f"Embedding simulado generado con {model} para texto de {len(clean_text)} caracteres")
            return embedding_vector

            # ========================================
            # CÓDIGO REAL DE OPENAI (DESCOMENTAR CUANDO TENGAS API KEY)
            # ========================================
            # response = await client.embeddings.create(
            #     model=model,
            #     input=clean_text,
            #     encoding_format="float"
            # )
            # logger.info(f"Embedding de OpenAI generado con {model} para texto de {len(clean_text)} caracteres")
            # return response.data[0].embedding
            # ========================================

        except Exception as e:
            logger.error(f"Error generando embedding: {e}")
            raise Exception(f"Error al generar embedding: {str(e)}")
    
    @staticmethod
    async def index_document(db: AsyncSession, document_id: UUID) -> Dict[str, Any]:
        try:
            result = await db.execute(select(Document).where(Document.id == document_id))
            document = result.scalar_one_or_none()
            
            if not document:
                raise ValueError(f"Documento con ID {document_id} no encontrado")
            
            if not document.full_text:
                raise ValueError(f"El documento {document_id} no tiene texto para indexar")
            
            # Obtener métricas del documento
            document_length = len(document.full_text)
            selected_model = IndexService._get_embedding_model(document_length)
            
            logger.info(f"Procesando documento {document_id} ({document_length} caracteres) con modelo {selected_model}")
            
            existing_chunks = await db.execute(
                select(DocumentChunk).where(DocumentChunk.document_id == document_id)
            )
            existing_chunks_list = existing_chunks.scalars().all()
            
            if existing_chunks_list:
                logger.info(f"Eliminando {len(existing_chunks_list)} chunks existentes para documento {document_id}")
                for chunk in existing_chunks_list:
                    await db.delete(chunk)
                await db.flush()
            
            chunks = IndexService._split_text_into_chunks(document.full_text)
            
            if not chunks:
                raise ValueError(f"No se pudieron generar chunks para el documento {document_id}")
            
            logger.info(f"Generando {len(chunks)} chunks para documento {document_id}")
            
            chunks_created = 0
            
            for i, chunk_text in enumerate(chunks):
                try:
                    logger.info(f"Procesando chunk {i+1}/{len(chunks)} para documento {document_id}")

                    # Pasar la longitud del documento completo para selección de modelo
                    embedding_vector = await IndexService._generate_embedding(chunk_text, document_length)
                    logger.info(f"Embedding generado para chunk {i+1}, dimensiones: {len(embedding_vector)}")

                    chunk = DocumentChunk(
                        document_id=document_id,
                        chunk_text=chunk_text,
                        embedding=embedding_vector
                    )

                    db.add(chunk)
                    await db.flush()

                    logger.info(f"Chunk {i+1} insertado exitosamente con ID: {chunk.id}")
                    chunks_created += 1
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error procesando chunk {i+1} del documento {document_id}: {str(e)}")
                    logger.error(f"Tipo de error: {type(e).__name__}")
                    continue
            
            await db.commit()
            logger.info(f"Commit realizado para documento {document_id}")

            verification_result = await db.execute(
                text("SELECT COUNT(*) FROM document_chunks WHERE document_id = :document_id"),
                {"document_id": str(document_id)}
            )
            actual_chunks_count = verification_result.scalar()
            logger.info(f"Verificación: {actual_chunks_count} chunks encontrados en BD para documento {document_id}")

            logger.info(f"Indexación completada para documento {document_id}: {chunks_created} chunks creados con modelo {selected_model}")
            
            return {
                "document_id": str(document_id),
                "chunks_indexed": chunks_created,
                "total_chunks": len(chunks),
                "embedding_model": selected_model,
                "document_size_chars": document_length
            }
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error indexando documento {document_id}: {e}")
            raise
    
    @staticmethod
    async def get_unindexed_documents(db: AsyncSession) -> List[Document]:
        try:
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
