"""asyncpg connection pool management.

Usage::

    pool = await create_pool(settings)
    # ... use pool ...
    await close_pool(pool)

The ``create_pool`` / ``close_pool`` pair is called from the FastAPI
lifespan handler in ``app.main``.
"""

from __future__ import annotations

import asyncpg

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger("storage.postgres")


async def create_pool(settings: Settings) -> asyncpg.Pool:
    """Create and return an asyncpg connection pool.

    The pool is configured from the ``postgres_*`` fields on *settings*.
    The initial DDL migration is applied automatically on first connect.
    """
    dsn = settings.postgres_dsn
    logger.info("Creating PostgreSQL connection pool", extra={"data": {"dsn": _mask_dsn(dsn)}})

    pool: asyncpg.Pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=2,
        max_size=10,
    )

    # Run the initial migration so the schema exists.
    await _apply_migrations(pool)

    return pool


async def close_pool(pool: asyncpg.Pool) -> None:
    """Gracefully close the connection pool."""
    logger.info("Closing PostgreSQL connection pool")
    await pool.close()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _apply_migrations(pool: asyncpg.Pool) -> None:
    """Execute the 001_init.sql migration idempotently."""
    import importlib.resources as pkg_resources
    import pathlib

    migrations_dir = pathlib.Path(__file__).parent / "migrations"
    init_sql = migrations_dir / "001_init.sql"

    if not init_sql.exists():
        logger.warning("Migration file not found, skipping", extra={"data": {"path": str(init_sql)}})
        return

    sql = init_sql.read_text(encoding="utf-8")
    async with pool.acquire() as conn:
        await conn.execute(sql)
    logger.info("Applied migration 001_init.sql")


def _mask_dsn(dsn: str) -> str:
    """Replace password in DSN with ``***`` for safe logging."""
    try:
        # postgresql://user:password@host:port/db
        if "@" in dsn and ":" in dsn.split("@")[0]:
            prefix, rest = dsn.split("@", 1)
            scheme_user = prefix.rsplit(":", 1)[0]
            return f"{scheme_user}:***@{rest}"
    except Exception:
        pass
    return dsn
