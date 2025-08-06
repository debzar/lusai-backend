from sqlalchemy import Column, Text, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text as sa_text
import uuid

from db.database import Base

class Case(Base):
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=sa_text("gen_random_uuid()"), unique=True, nullable=False)
    original_name = Column(Text, nullable=False)
    storage_url = Column(Text, nullable=False)
    text = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    token_count = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Case(id={self.id}, original_name='{self.original_name}')>"
