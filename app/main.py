from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db

app = FastAPI()

@app.get("/ping-db")
async def ping_db(session: AsyncSession = Depends(get_db)):
    try:
        await session.execute(text("SELECT 1"))  # 👈 usa text("...")
        return {"ok": True, "message": "Conexión exitosa con la base de datos"}
    except Exception as e:
        return {"ok": False, "error": str(e)}