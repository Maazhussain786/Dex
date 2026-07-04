from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, HttpUrl

from app.domain.models import Project, ProjectStatus


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

_PROJECTS: dict[str, Project] = {}


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: CreateProjectRequest) -> ProjectResponse:
    project = Project.create(
        name=payload.name,
        target_url=str(payload.target_url),
        description=payload.description,
    )
    _PROJECTS[project.id] = project
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.get("", response_model=list[ProjectResponse])
def list_projects() -> list[ProjectResponse]:
    return [ProjectResponse.model_validate(project, from_attributes=True) for project in _PROJECTS.values()]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str) -> ProjectResponse:
    project = _PROJECTS.get(project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return ProjectResponse.model_validate(project, from_attributes=True)
