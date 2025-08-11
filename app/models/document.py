"""
Modelo de documentos para la base de datos.
Representa archivos subidos con su metadata y texto extraído.
"""
from sqlalchemy import Column, String, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.database import Base

class Document(Base):
    """Modelo para la tabla documents que almacena documentos y su texto extraído"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    url = Column(Text, nullable=False)
    content_type = Column(String, nullable=False)
    text_preview = Column(Text)
    full_text = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}')>"
    
    def to_dict(self):
        """Convierte el modelo a un diccionario para la API"""
        return {
            "id": str(self.id),
            "filename": self.filename,
            "url": self.url,
            "content_type": self.content_type,
            "text_preview": self.text_preview,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
