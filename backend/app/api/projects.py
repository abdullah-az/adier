from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_project_service
from app.schemas.project import ProjectSummaryResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectSummaryResponse])
async def list_projects(
    project_service: ProjectService = Depends(get_project_service),
) -> List[ProjectSummaryResponse]:
    """Return a summary view for all known projects."""
    return await project_service.list_projects()


@router.get("/{project_id}", response_model=ProjectSummaryResponse)
async def get_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> ProjectSummaryResponse:
    """Return a summary for a specific project."""
    summary = await project_service.get_project(project_id)
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return summary
