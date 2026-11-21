# db/db.py
import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
from db.tls_contract import asyncpg_connection_options
from sqlalchemy.orm import sessionmaker
import config  # triggers layered .env loading and debug output

# ────────────────────────────────────────────────────────────────
# 🛠 Fix DATABASE_URL scheme if Render injects 'postgres://'
# ────────────────────────────────────────────────────────────────
raw_url = (os.getenv("DATABASE_URL") or "").strip()
if not raw_url:
    raise RuntimeError("PARSER_DATABASE_URL_REQUIRED")

if raw_url.startswith("postgres://"):
    raw_url = "postgresql+asyncpg://" + raw_url[len("postgres://"):]
elif raw_url.startswith("postgresql://"):
    raw_url = "postgresql+asyncpg://" + raw_url[len("postgresql://"):]
if not raw_url.startswith("postgresql+asyncpg://"):
    raise RuntimeError("PARSER_ASYNC_DATABASE_DRIVER_REQUIRED")

DATABASE_URL = raw_url

# ────────────────────────────────────────────────────────────────
# 🌐 SSL Context for Remote DB
# ────────────────────────────────────────────────────────────────
connect_args = asyncpg_connection_options(DATABASE_URL)

# ────────────────────────────────────────────────────────────────
# 🚀 SQLAlchemy Async Engine + Session
# ────────────────────────────────────────────────────────────────
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    pool_pre_ping=True,            
    pool_recycle=300,            
    pool_timeout=30,                
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ────────────────────────────────────────────────────────────────
# 📦 DB Init w/ Retry for Render cold-start race condition
# ────────────────────────────────────────────────────────────────
import asyncpg
import asyncio

async def init_db_async():
    retries = 5
    for attempt in range(retries):
        try:
            # Web startup is deliberately read-only in EVERY environment.
            # Reviewed Alembic migrations are a separate, explicitly authorized action.
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            logging.info("Parser database read-only startup check completed.")
            return
        except asyncpg.exceptions.ConnectionDoesNotExistError:
            # Never report successful startup after an exhausted DB retry budget.
            # Do not include exception text: provider errors can contain secrets.
            logging.warning(
                "Parser database connection dropped (%d/%d)",
                attempt + 1,
                retries,
            )
            if attempt + 1 == retries:
                raise RuntimeError("PARSER_DB_STARTUP_RETRIES_EXHAUSTED") from None
            await asyncio.sleep(2)
        except Exception as e:
            logging.error("Parser database initialization failed: %s", type(e).__name__)
            raise

# ────────────────────────────────────────────────────────────────
# 🤝 DB Session Dependency
# ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    FastAPI dependency: yields an AsyncSession.
    """
    async with async_session() as session:
        yield session

# ────────────────────────────────────────────────────────────────
# (Re-added) AsyncSession provider for routes that need it
# ────────────────────────────────────────────────────────────────
async def get_async_session() -> AsyncSession:
    """
    Alternate FastAPI dependency if you explicitly want an "async_session" name.
    """
    async with async_session() as session:
        yield session

# ────────────────────────────────────────────────────────────────
# 🔍 Example Helper Functions
# ────────────────────────────────────────────────────────────────
async def get_user_by_uid(uid: str):
    from db.models import User
    async with async_session() as session:
        result = await session.execute(
            User.__table__.select().where(User.uid == uid)
        )
        return result.scalar_one_or_none()

async def get_user_by_email(email: str):
    from db.models import User
    async with async_session() as session:
        result = await session.execute(
            User.__table__.select().where(User.email == email)
        )
        return result.scalar_one_or_none()
