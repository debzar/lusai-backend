"""
Modelo de chunks de documentos para la base de datos.
Representa fragmentos de texto de documentos con sus embeddings.
"""
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.database import Base

class DocumentChunk(Base):
    """Modelo para la tabla document_chunks que almacena fragmentos de texto con embeddings"""
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column("embedding", Text)  # Almacenamos el vector como texto JSON por compatibilidad
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relación con Document
    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id})>"
    
    def to_dict(self):
        """Convierte el modelo a un diccionario para la API"""
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "chunk_text": self.chunk_text[:100] + "..." if len(self.chunk_text) > 100 else self.chunk_text,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
