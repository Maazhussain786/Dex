"""Exploration session endpoints.

Provides CRUD operations for sessions and an endpoint to trigger
asynchronous exploration.  Evidence can be retrieved in a paginated
fashion.  A WebSocket endpoint streams live exploration progress.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from app.core.logging import get_logger
from app.domain.models import ExplorationSession, EvidenceType, ProjectStatus
from app.exploration.contracts import ExplorationStatus, ExplorationTarget
from app.storage.contracts import EvidenceRepository, GraphRepository, ProjectRepository, SessionRepository

logger = get_logger("api.sessions")

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    max_depth: int = 3
    screenshot_enabled: bool = True
    network_capture_enabled: bool = True


class SessionResponse(BaseModel):
    id: str
    project_id: str
    started_at: datetime
    completed_at: datetime | None


class EvidenceResponse(BaseModel):
    id: str
    project_id: str
    session_id: str
    evidence_type: EvidenceType
    summary: str
    collected_at: datetime


class SessionProgressResponse(BaseModel):
    status: str
    pages_visited: int
    evidence_collected: int
    current_url: str


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def _get_project_repo(request: Request) -> ProjectRepository:
    return request.app.state.project_repo


def _get_session_repo(request: Request) -> SessionRepository:
    return request.app.state.session_repo


def _get_evidence_repo(request: Request) -> EvidenceRepository:
    return request.app.state.evidence_repo


def _get_neo4j_repo(request: Request) -> GraphRepository | None:
    return getattr(request.app.state, "neo4j_repo", None)


# ---------------------------------------------------------------------------
# Background exploration task
# ---------------------------------------------------------------------------

# Track exploration progress per session for the WebSocket endpoint.
_exploration_progress: dict[str, dict[str, object]] = {}


async def _run_exploration(
    target: ExplorationTarget,
    session_repo: SessionRepository,
    evidence_repo: EvidenceRepository,
    project_repo: ProjectRepository,
    neo4j_repo: GraphRepository | None = None,
) -> None:
    """Run Playwright exploration as a background task.

    Imports ``PlaywrightExplorer`` lazily so the module-level import
    does not require Playwright to be installed.
    """
    session_id = target.session_id
    _exploration_progress[session_id] = {
        "status": "running",
        "pages_visited": 0,
        "evidence_collected": 0,
        "current_url": target.url,
    }

    try:
        await project_repo.update_status(target.project_id, ProjectStatus.EXPLORING)

        from app.exploration.browser_explorer import PlaywrightExplorer

        explorer = PlaywrightExplorer()
        report = await explorer.explore(target)

        # Persist all collected evidence.
        if report.evidence:
            await evidence_repo.save_many(list(report.evidence))

        # Build knowledge graph if Neo4j is available.
        if neo4j_repo is not None:
            try:
                from app.graph import ApiGraphBuilder, ComponentGraphBuilder, NavigationGraphBuilder
                builders = [NavigationGraphBuilder(), ApiGraphBuilder(), ComponentGraphBuilder()]
                
                for builder in builders:
                    nodes, edges = builder.build(report)
                    for node in nodes:
                        await neo4j_repo.save_node(node)
                    for edge in edges:
                        await neo4j_repo.save_edge(edge)
                        
                logger.info("Knowledge graph updated", extra={"data": {"session_id": session_id}})
            except Exception:
                logger.exception("Failed to build or save knowledge graph")

        # Mark session completed.
        await session_repo.mark_completed(session_id)

        final_status = "completed" if report.status == ExplorationStatus.COMPLETED else "failed"
        project_status = ProjectStatus.READY if final_status == "completed" else ProjectStatus.FAILED
        await project_repo.update_status(target.project_id, project_status)

        _exploration_progress[session_id] = {
            "status": final_status,
            "pages_visited": report.pages_visited,
            "evidence_collected": len(report.evidence),
            "current_url": "",
        }

        logger.info(
            "Background exploration finished",
            extra={"data": {
                "session_id": session_id,
                "status": final_status,
                "pages": report.pages_visited,
                "evidence": len(report.evidence),
            }},
        )

    except Exception as exc:
        logger.exception("Background exploration failed")
        _exploration_progress[session_id] = {
            "status": "failed",
            "pages_visited": 0,
            "evidence_collected": 0,
            "current_url": "",
        }
        try:
            await project_repo.update_status(target.project_id, ProjectStatus.FAILED)
            await session_repo.mark_completed(session_id)
        except Exception:
            logger.exception("Failed to update status after exploration error")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post(
    "/{project_id}/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    project_id: str,
    payload: CreateSessionRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> SessionResponse:
    """Create a session and trigger async exploration."""
    project_repo = _get_project_repo(request)
    session_repo = _get_session_repo(request)
    evidence_repo = _get_evidence_repo(request)
    neo4j_repo = _get_neo4j_repo(request)

    # Verify the project exists.
    project = await project_repo.get(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Create session.
    session = ExplorationSession.start(project_id)
    await session_repo.save(session)

    # Build exploration target and dispatch background task.
    target = ExplorationTarget(
        project_id=project_id,
        session_id=session.id,
        url=project.target_url,
        max_depth=payload.max_depth,
        screenshot_enabled=payload.screenshot_enabled,
        network_capture_enabled=payload.network_capture_enabled,
    )
    background_tasks.add_task(_run_exploration, target, session_repo, evidence_repo, project_repo, neo4j_repo)

    logger.info(
        "Session created, exploration queued",
        extra={"data": {"project_id": project_id, "session_id": session.id}},
    )

    return SessionResponse(
        id=session.id,
        project_id=session.project_id,
        started_at=session.started_at,
        completed_at=session.completed_at,
    )


@router.get("/{project_id}/sessions/{session_id}", response_model=SessionResponse)
async def get_session(project_id: str, session_id: str, request: Request) -> SessionResponse:
    """Return session status."""
    session_repo = _get_session_repo(request)
    session = await session_repo.get(session_id)
    if session is None or session.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return SessionResponse(
        id=session.id,
        project_id=session.project_id,
        started_at=session.started_at,
        completed_at=session.completed_at,
    )


@router.get("/{project_id}/sessions/{session_id}/evidence", response_model=list[EvidenceResponse])
async def list_evidence(
    project_id: str,
    session_id: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
) -> list[EvidenceResponse]:
    """Return paginated evidence for a session."""
    session_repo = _get_session_repo(request)
    evidence_repo = _get_evidence_repo(request)

    # Verify the session exists and belongs to the project.
    session = await session_repo.get(session_id)
    if session is None or session.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    items = await evidence_repo.list_by_session(session_id, limit=limit, offset=offset)
    return [
        EvidenceResponse(
            id=item.id,
            project_id=item.project_id,
            session_id=item.session_id,
            evidence_type=item.evidence_type,
            summary=item.summary,
            collected_at=item.collected_at,
        )
        for item in items
    ]


@router.websocket("/{project_id}/sessions/{session_id}/stream")
async def session_stream(websocket: WebSocket, project_id: str, session_id: str) -> None:
    """WebSocket endpoint for live exploration progress.

    Sends JSON status updates every second while the exploration is running.
    Closes automatically when the exploration completes or fails.
    """
    await websocket.accept()

    try:
        while True:
            progress = _exploration_progress.get(session_id)
            if progress is None:
                await websocket.send_json({
                    "status": "unknown",
                    "pages_visited": 0,
                    "evidence_collected": 0,
                    "current_url": "",
                })
            else:
                await websocket.send_json(progress)

                if progress.get("status") in ("completed", "failed"):
                    break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info(
            "WebSocket client disconnected",
            extra={"data": {"session_id": session_id}},
        )
    finally:
        # Clean up progress data for completed sessions.
        _exploration_progress.pop(session_id, None)
