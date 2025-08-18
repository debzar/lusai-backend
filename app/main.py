import logging
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db, engine, Base
from contextlib import asynccontextmanager
from app.routes import upload, scraping  # Agregando el router de scraping

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Se ejecuta al iniciar la app
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # 👈 Aquí arranca la app
    # Aquí puedes cerrar conexiones si necesitas
    await engine.dispose()

app = FastAPI(
    title="IUSAI API",
    description="API para la gestión de documentos legales",
    version="0.1.0",
    lifespan=lifespan
)

# Incluir las rutas
app.include_router(upload.router, prefix="/api/files", tags=["files"])
app.include_router(scraping.router)

@app.get("/")
def root():
    return {"message": "API de IUSAI activa", "docs": "/docs"}

@app.get("/ping-db")
async def ping_db(session: AsyncSession = Depends(get_db)):
    try:
        await session.execute(text("SELECT 1"))
        return {"ok": True, "message": "Conexión exitosa con la base de datos"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
