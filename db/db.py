import os
import logging
import ssl
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
from fastapi import Depends

# ------------------------------------------------------------------------
# Load DB URL from the environment, stripping extraneous whitespace/newlines.
# If not set, use the fallback external Render URL with literal credentials.
# Note: Do not include "?sslmode=require" in the URL because asyncpg does not accept it.
# SSL will be provided via the ssl_context.
# ------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://aoe2hd_db_user:GvoxmmKHfCMOKVKBkpx6c1mQrQZ5hHHN@dpg-cvo1fgeuk2gs73bgj3eg-a.oregon-postgres.render.com:5432/aoe2hd_db"
).strip()

# ------------------------------------------------------------------------
# Create a default SSL context for secure connections.
# ------------------------------------------------------------------------
ssl_context = ssl.create_default_context()

# ------------------------------------------------------------------------
# Create the async engine and sessionmaker, providing the SSL context.
# ------------------------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"ssl": ssl_context}
)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# ------------------------------------------------------------------------
# Async DB Initialization: Create all tables using the declarative Base.
# ------------------------------------------------------------------------
async def init_db_async():
    try:
        # Delayed import to avoid circular dependency issues.
        from db.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logging.info("✅ Async tables created.")
    except Exception as e:
        logging.error(f"❌ Failed to initialize DB async: {e}")
        raise

# ------------------------------------------------------------------------
# Dependency: Provide an async DB session.
# ------------------------------------------------------------------------
@asynccontextmanager
async def get_db():
    async with async_session() as session:
        yield session

# ------------------------------------------------------------------------
# Example helper method: Retrieve a user by UID.
# ------------------------------------------------------------------------
async def get_user_by_uid(uid: str):
    from db.models import User
    async with async_session() as session:
        result = await session.execute(
            User.__table__.select().where(User.uid == uid)
        )
        return result.scalar_one_or_none()

# ------------------------------------------------------------------------
# Example helper method: Retrieve a user by email.
# ------------------------------------------------------------------------
async def get_user_by_email(email: str):
    from db.models import User
    async with async_session() as session:
        result = await session.execute(
            User.__table__.select().where(User.email == email)
        )
        return result.scalar_one_or_none()
