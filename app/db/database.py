from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Crear el engine con configuración para evitar problemas de prepared statements
engine = create_async_engine(
    DATABASE_URL, 
    echo=True,
    pool_pre_ping=True,  # Verificar conexiones antes de usar
    pool_size=5,         # Tamaño del pool
    max_overflow=10,     # Conexiones adicionales permitidas
    # Configuración específica para evitar problemas con pgbouncer
    connect_args={
        "statement_cache_size": 0,  # Deshabilitar cache de prepared statements
        "prepared_statement_cache_size": 0,  # Deshabilitar cache de prepared statements
    }
)

# Crear sesión asincrónica
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative base
Base = declarative_base()

# Dependencia para obtener una sesión en cada request
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session