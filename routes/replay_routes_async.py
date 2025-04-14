from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_db
from db.models import GameStats
from datetime import datetime
import json

router = APIRouter(prefix="/api", tags=["replay"])


class ParseReplayRequest(BaseModel):
    replay_file: str
    replay_hash: str
    parse_iteration: int = 0
    is_final: bool = False
    game_version: str | None = None
    map_name: str = "Unknown"
    map_size: str = "Unknown"
    game_type: str | None = None
    duration: int = 0
    winner: str = "Unknown"
    players: list = []
    played_on: str | None = None


@router.post("/parse_replay")
async def parse_new_replay(data: ParseReplayRequest, db_gen=Depends(get_db)):
    async with db_gen as db:
        if data.is_final:
            existing = await db.execute(
                select(GameStats).where(
                    GameStats.replay_hash == data.replay_hash,
                    GameStats.is_final.is_(True),
                )
            )
            if existing.scalars().first():
                return {"message": "Replay already parsed as final. Skipped."}

        game = GameStats(
            replay_file=data.replay_file,
            replay_hash=data.replay_hash,
            game_version=data.game_version,
            map=json.dumps({"name": data.map_name, "size": data.map_size}),
            game_type=data.game_type,
            duration=data.duration,
            winner=data.winner,
            players=json.dumps(data.players),
            parse_iteration=data.parse_iteration,
            is_final=data.is_final,
            played_on=(
                datetime.fromisoformat(data.played_on) if data.played_on else None
            ),
        )
        db.add(game)
        await db.commit()

        return {"message": f"Replay stored (iteration {data.parse_iteration})"}


@router.get("/health")
async def health_check():
    return {"status": "ok"}
