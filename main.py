from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging

from db.db import init_db_async, get_db
from db.models import GameStats
from routes import (
    user_me,
    user_routes_async,
    replay_routes_async,
    debug_routes_async,
    admin_routes_async,
)

app = FastAPI()

# ───────────────────────────────────────────────
# 🌐 Enable CORS
# ───────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "https://aoe2-betting.vercel.app",
        "https://aoe2hd-frontend.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ───────────────────────────────────────────────
# 🔌 Async DB Init
# ───────────────────────────────────────────────
@app.on_event("startup")
async def startup_event():
    await init_db_async()

# ───────────────────────────────────────────────
# 📦 Include All Routers
# ───────────────────────────────────────────────
app.include_router(user_me.router)
app.include_router(user_routes_async.router)
app.include_router(replay_routes_async.router)
app.include_router(debug_routes_async.router)
app.include_router(admin_routes_async.router)

# ───────────────────────────────────────────────
# 🧪 Root Test Route
# ───────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "AoE2 Betting Backend is running!"}

# ───────────────────────────────────────────────
# 📊 Postgres-Backed Game Stats Endpoint
# ───────────────────────────────────────────────
@app.get("/api/game_stats")
async def get_game_stats(db_gen=Depends(get_db)):
    try:
        async with db_gen as db:  # ✅ unlocks the session
            result = await db.execute(select(GameStats).order_by(GameStats.timestamp.desc()))
            games = result.scalars().all()
            from logging import getLogger
            logger = getLogger(__name__)
            logger.info(f"📊 Returning {len(games)} games from DB")
            return [g.to_dict() for g in games]
    except Exception as e:
        import logging
        logging.error(f"❌ Failed to fetch game stats: {e}", exc_info=True)
        return []

