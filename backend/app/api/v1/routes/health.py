from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health():
    # Is the API running?
    return{"status" : "ok"}

@router.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    # Can the API reach the database?
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="Database not reachable")
    return {"status": "ok", "database": "connected"}