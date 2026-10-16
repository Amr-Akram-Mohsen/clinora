"""
migrations/env.py

Alembic migration environment.

This file:
1. Loads the DATABASE_URL from the .env file (via dotenv) so migrations
   work without manually exporting env vars.
2. Imports all ORM models via the model registry so autogenerate detects them.
3. Runs in async mode using asyncpg — consistent with the application engine.
"""

import asyncio
import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models so Alembic's autogenerate sees them
import infrastructure.database.models  # noqa: F401
from infrastructure.database.base import Base

# Load .env so DATABASE_URL is available
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

config = context.config

db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://clinora:clinora@localhost:5432/clinora")
config.set_main_option("sqlalchemy.url", db_url)


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
