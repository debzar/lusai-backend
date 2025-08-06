from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Crear el engine
engine = create_async_engine(DATABASE_URL, echo=True)

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