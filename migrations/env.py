import sys
import os
import asyncio
import json
import pathlib
from logging.config import fileConfig

# Add project root to sys.path so 'db' can be imported
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from alembic import context
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import create_engine
from dotenv import load_dotenv

from db.models import Base  # now resolvable after sys.path fix
from db.tls_contract import asyncpg_connection_options, sync_postgres_connection_options

# Load .env if it exists
dotenv_path = pathlib.Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

# Resolve database URL from Alembic CLI args, config.json, env, or fallback
cli_args = context.get_x_argument(as_dictionary=True)
DB_URL = cli_args.get("db_url") or os.getenv("DATABASE_URL")

if not DB_URL:
    raise RuntimeError("PARSER_DATABASE_URL_REQUIRED")
if DB_URL.startswith("postgres://"):
    DB_URL = "postgresql+asyncpg://" + DB_URL[len("postgres://"):]

# Alembic config object
config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=DB_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(sync_connection):
    context.configure(
        connection=sync_connection,
        target_metadata=target_metadata,
    )
    context.run_migrations()

async def run_migrations_online():
    # Never copy a credential-bearing URL into the Alembic config/logging.
    # Alembic runs before uvicorn; it must enforce the same TLS policy as db/db.py.
    if DB_URL.startswith("postgresql+asyncpg://"):
        connectable: AsyncEngine = create_async_engine(
            DB_URL, future=True, connect_args=asyncpg_connection_options(DB_URL)
        )
        try:
            async with connectable.begin() as conn:
                await conn.run_sync(do_run_migrations)
        finally:
            await connectable.dispose()
    else:
        connectable = create_engine(
            DB_URL, future=True, connect_args=sync_postgres_connection_options(DB_URL)
        )
        try:
            with connectable.begin() as conn:
                do_run_migrations(conn)
        finally:
            connectable.dispose()


def run_async():
    asyncio.run(run_migrations_online())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_async()
