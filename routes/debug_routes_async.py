from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import GameStats, User
from db.db import get_db

router = APIRouter(prefix="/debug", tags=["Debug"])


@router.get("/game_count")
async def debug_count(db_gen=Depends(get_db)):
    async with db_gen as db:
        total = await db.scalar(select(func.count()).select_from(GameStats))
        finals = await db.scalar(
            select(func.count())
            .select_from(GameStats)
            .where(GameStats.is_final.is_(True))
        )
        return {"total_games": total, "final_games": finals}


@router.delete("/delete_all")
async def delete_all():
    # This API has no data-deletion authority under the production trust model.
    raise HTTPException(status_code=410, detail="Destructive debug route permanently retired")
