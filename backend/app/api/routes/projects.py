"""Project CRUD endpoints.

Backed by :class:`ProjectRepository` injected via ``app.state``.
"""

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, HttpUrl

from app.domain.models import Project, ProjectStatus
from app.storage.contracts import ProjectRepository


class CreateProjectRequest(BaseModel):
    name: str
    target_url: HttpUrl
    description: str | None = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    target_url: str
    description: str | None
    status: ProjectStatus


router = APIRouter()


def _get_project_repo(request: Request) -> ProjectRepository:
    """Extract the project repository from app state."""
    return request.app.state.project_repo


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: CreateProjectRequest, request: Request) -> ProjectResponse:
    repo = _get_project_repo(request)
    project = Project.create(
        name=payload.name,
        target_url=str(payload.target_url),
        description=payload.description,
    )
    await repo.save(project)
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(request: Request) -> list[ProjectResponse]:
    repo = _get_project_repo(request)
    projects = await repo.list_all()
    return [ProjectResponse.model_validate(project, from_attributes=True) for project in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, request: Request) -> ProjectResponse:
    repo = _get_project_repo(request)
    project = await repo.get(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse.model_validate(project, from_attributes=True)
