from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "service": "PBIP API",
            "database": "connected",
        }

    except Exception:
        return {
            "status": "degraded",
            "service": "PBIP API",
            "database": "disconnected",
        }