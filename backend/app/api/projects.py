from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_project_service
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectSummary,
    ProjectUpdateRequest,
)
from app.services.project_service import ProjectService
from app.utils.responses import empty_response, error_response, paginated_response, success_response

router = APIRouter(prefix="/projects", tags=["projects"])


def _validate_sort(sort_order: str) -> str:
    order = sort_order.lower()
    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort order")
    return order


@router.get(
    "",
    response_model=PaginatedResponse[ProjectSummary],
    summary="List projects",
    response_description="Paginated list of projects",
)
async def list_projects(
    project_service: ProjectService = Depends(get_project_service),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort_by: str | None = Query(None, pattern="^(name|created_at|updated_at|status)$"),
    sort_order: str = Query("asc"),
    locale: str | None = Query(None, description="Filter by locale"),
) -> PaginatedResponse[ProjectSummary]:
    order = _validate_sort(sort_order)
    projects, total = await project_service.list_projects(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=order,
        locale=locale,
    )
    items = [ProjectSummary.from_model(project) for project in projects]
    return paginated_response(
        items,
        page=page,
        page_size=page_size,
        total_items=total,
        sort_by=sort_by,
        sort_order=order,
        locale=locale,
        message="Projects retrieved",
    )


@router.post(
    "",
    response_model=ApiResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
)
async def create_project(
    payload: ProjectCreateRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> ApiResponse[ProjectResponse]:
    project = await project_service.create_project(
        name=payload.name,
        description=payload.description,
        locale=payload.locale,
        tags=payload.tags,
        status=payload.status,
        metadata=payload.metadata,
        default_aspect_ratio=payload.default_aspect_ratio,
        default_resolution=payload.default_resolution,
    )
    return success_response(
        ProjectResponse.from_model(project),
        message="Project created",
        code="PROJECT_CREATED",
    )


@router.get(
    "/{project_id}",
    response_model=ApiResponse[ProjectResponse],
    summary="Get project details",
)
async def get_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> ApiResponse[ProjectResponse]:
    project = await project_service.get_project(project_id)
    if project is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="PROJECT_NOT_FOUND", message="Project not found")
    return success_response(
        ProjectResponse.from_model(project),
        message="Project fetched",
    )


@router.patch(
    "/{project_id}",
    response_model=ApiResponse[ProjectResponse],
    summary="Update a project",
)
async def update_project(
    project_id: str,
    payload: ProjectUpdateRequest,
    project_service: ProjectService = Depends(get_project_service),
) -> ApiResponse[ProjectResponse]:
    project = await project_service.update_project(
        project_id,
        name=payload.name,
        description=payload.description,
        locale=payload.locale,
        status=payload.status,
        tags=payload.tags,
        metadata=payload.metadata,
        default_aspect_ratio=payload.default_aspect_ratio,
        default_resolution=payload.default_resolution,
    )
    if project is None:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="PROJECT_NOT_FOUND", message="Project not found")
    return success_response(ProjectResponse.from_model(project), message="Project updated")


@router.delete(
    "/{project_id}",
    response_model=ApiResponse[None],
    summary="Delete a project",
)
async def delete_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
) -> ApiResponse[None]:
    deleted = await project_service.delete_project(project_id)
    if not deleted:
        return error_response(status_code=status.HTTP_404_NOT_FOUND, code="PROJECT_NOT_FOUND", message="Project not found")
    return empty_response(message="Project deleted", code="PROJECT_DELETED")
