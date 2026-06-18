"""
Alembic env.py — настроен для async SQLAlchemy.

Автоматически берёт DATABASE_URL из app.config.
Импортирует все модели через app.models для autogenerate.
"""

import asyncio
import os
import sys
from logging.config import fileConfig

# Добавляем корень проекта в PYTHONPATH, чтобы alembic видел папку app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import get_settings
from app.models import Base  # noqa: F401 — нужен для autogenerate

# Alembic Config object
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata для autogenerate
target_metadata = Base.metadata

# Подставляем URL из нашего конфига
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """Миграции в offline режиме (генерация SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Запуск миграций с соединением."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Async миграции через asyncpg."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Миграции в online режиме (async)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
