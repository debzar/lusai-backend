"""
Modelo de chunks de documentos para la base de datos.
"""
from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid

from app.db.database import Base

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    document = relationship("Document", back_populates="chunks")

    def __repr__(self):
        return f"<DocumentChunk(id={self.id}, document_id={self.document_id})>"

    def to_dict(self):
        return {
            "id": str(self.id),
            "document_id": str(self.document_id),
            "chunk_text": self.chunk_text[:100] + "..." if len(self.chunk_text) > 100 else self.chunk_text,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
