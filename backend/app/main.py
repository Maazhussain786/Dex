from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.projects import router as projects_router
from app.api.routes.sessions import router as sessions_router
from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.storage.postgres.connection import close_pool, create_pool
from app.storage.postgres.evidence_repo import PgEvidenceRepository
from app.storage.postgres.project_repo import PgProjectRepository
from app.storage.postgres.session_repo import PgSessionRepository

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage database connections across the application lifecycle."""
    settings = get_settings()
    setup_logging(settings.log_level)

    logger.info("Starting Dex backend", extra={"data": {"env": settings.environment}})

    # -- Startup: create connection pools and repositories ---------------
    pg_pool = await create_pool(settings)
    app.state.pg_pool = pg_pool
    app.state.project_repo = PgProjectRepository(pg_pool)
    app.state.session_repo = PgSessionRepository(pg_pool)
    app.state.evidence_repo = PgEvidenceRepository(pg_pool)

    # Neo4j and Qdrant are initialised lazily — the adapters are
    # created here but they open connections on first use.
    # Full integration is done when those services are actually needed
    # (Phase 7+ for Neo4j, Phase 8+ for Qdrant).
    app.state.neo4j_repo = None
    app.state.qdrant_repo = None

    try:
        # Attempt Neo4j connection (non-fatal if unavailable)
        try:
            from app.storage.neo4j.graph_repo import Neo4jGraphRepository

            app.state.neo4j_repo = await Neo4jGraphRepository.create(settings)
        except Exception as exc:
            logger.warning(
                "Neo4j unavailable — graph features disabled",
                extra={"data": {"error": str(exc)}},
            )

        # Attempt Qdrant connection (non-fatal if unavailable)
        try:
            from app.storage.qdrant.vector_repo import QdrantVectorRepository

            app.state.qdrant_repo = await QdrantVectorRepository.create(settings)
        except Exception as exc:
            logger.warning(
                "Qdrant unavailable — vector search disabled",
                extra={"data": {"error": str(exc)}},
            )

        yield

    finally:
        # -- Shutdown: close all connections ------------------------------
        await close_pool(pg_pool)

        if app.state.neo4j_repo is not None:
            await app.state.neo4j_repo.close()

        if app.state.qdrant_repo is not None:
            await app.state.qdrant_repo.close()

        logger.info("Dex backend shut down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Dex API",
        version="0.1.0",
        description="Evidence-first software understanding platform.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix="/health", tags=["health"])
    app.include_router(projects_router, prefix="/projects", tags=["projects"])
    app.include_router(sessions_router, prefix="/projects", tags=["sessions"])
    return app


app = create_app()
