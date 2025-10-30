from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.errors import ConflictError, ResourceNotFoundError
from ...models.clip import Clip, ClipVersion
from ...models.enums import ProcessingJobStatus
from ...models.project import Project
from ...repositories.project import ProjectRepository
from ...schemas.pagination import PaginatedResponse
from ...schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
) -> ProjectRead:
    """
    Create a new project.
    
    Args:
        project_in: Project creation data
        db: Database session
        
    Returns:
        Created project with generated ID and timestamps
    """
    repository = ProjectRepository(db)
    project = repository.create(project_in)
    
    logger.info(
        "Project created",
        extra={"project_id": project.id, "name": project.name},
    )
    
    return ProjectRead.model_validate(project)


@router.get("/", response_model=PaginatedResponse[ProjectRead])
async def list_projects(
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
) -> PaginatedResponse[ProjectRead]:
    """
    List projects with pagination.
    
    Args:
        offset: Number of projects to skip
        limit: Maximum number of projects to return (1-100)
        db: Database session
        
    Returns:
        Paginated list of projects
    """
    total_stmt = select(func.count()).select_from(Project)
    total = db.execute(total_stmt).scalar() or 0
    
    stmt = (
        select(Project)
        .order_by(Project.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    
    result = db.execute(stmt)
    projects = result.scalars().all()
    
    return PaginatedResponse[ProjectRead](
        items=[ProjectRead.model_validate(project) for project in projects],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> ProjectRead:
    """
    Get a specific project by ID.
    
    Args:
        project_id: Project identifier
        db: Database session
        
    Returns:
        Project details
        
    Raises:
        ResourceNotFoundError: If project is not found
    """
    repository = ProjectRepository(db)
    project = repository.get(project_id)
    
    if project is None:
        raise ResourceNotFoundError("Project", project_id)
    
    return ProjectRead.model_validate(project)


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
) -> ProjectRead:
    """
    Update a project.
    
    Args:
        project_id: Project identifier
        project_in: Project update data
        db: Database session
        
    Returns:
        Updated project
        
    Raises:
        ResourceNotFoundError: If project is not found
    """
    repository = ProjectRepository(db)
    project = repository.get(project_id)
    
    if project is None:
        raise ResourceNotFoundError("Project", project_id)
    
    updated_project = repository.update(project, project_in)
    
    logger.info(
        "Project updated",
        extra={"project_id": project_id},
    )
    
    return ProjectRead.model_validate(updated_project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a project.
    
    Args:
        project_id: Project identifier
        db: Database session
        
    Raises:
        ResourceNotFoundError: If project is not found
        ConflictError: If project has active processing jobs
    """
    repository = ProjectRepository(db)
    project = repository.get(project_id)
    
    if project is None:
        raise ResourceNotFoundError("Project", project_id)
    
    active_job_count = _count_active_jobs_for_project(db, project_id)
    
    if active_job_count > 0:
        raise ConflictError(
            f"Cannot delete project with {active_job_count} active processing job(s). "
            "Please wait for jobs to complete or cancel them first."
        )
    
    repository.delete(project)
    
    logger.info(
        "Project deleted",
        extra={"project_id": project_id},
    )


def _count_active_jobs_for_project(db: Session, project_id: str) -> int:
    """Count active processing jobs for a project."""
    from ...models.processing_job import ProcessingJob
    
    active_statuses = [
        ProcessingJobStatus.PENDING,
        ProcessingJobStatus.QUEUED,
        ProcessingJobStatus.IN_PROGRESS,
    ]
    
    stmt = (
        select(func.count())
        .select_from(ProcessingJob)
        .join(ClipVersion, ProcessingJob.clip_version_id == ClipVersion.id)
        .join(Clip, ClipVersion.clip_id == Clip.id)
        .where(
            Clip.project_id == project_id,
            ProcessingJob.status.in_(active_statuses),
        )
    )
    
    result = db.execute(stmt)
    return result.scalar() or 0


__all__ = ["router"]
