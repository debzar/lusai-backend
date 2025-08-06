from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db, engine, Base
from contextlib import asynccontextmanager
from routes import upload  # Importa el router correctamente

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Se ejecuta al iniciar la app
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # 👈 Aquí arranca la app

    # Aquí puedes cerrar conexiones si necesitas

app = FastAPI(lifespan=lifespan)
app.include_router(upload.router, prefix="/api", tags=["upload"])

@app.get("/")
def root():
    return {"message": "API de subida de archivos activa"}

@app.get("/ping-db")
async def ping_db(session: AsyncSession = Depends(get_db)):
    try:
        await session.execute(text("SELECT 1"))
        return {"ok": True, "message": "Conexión exitosa con la base de datos"}
    except Exception as e:
        return {"ok": False, "error": str(e)}
