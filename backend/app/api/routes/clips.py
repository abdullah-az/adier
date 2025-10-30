from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.errors import ResourceNotFoundError
from ...models.clip import Clip
from ...repositories.clip import ClipRepository
from ...schemas.clip import ClipRead
from ...schemas.pagination import PaginatedResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/clips", tags=["clips"])


@router.get("/", response_model=PaginatedResponse[ClipRead])
async def list_clips(
    project_id: Annotated[Optional[str], Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
) -> PaginatedResponse[ClipRead]:
    """
    List clips with optional project filtering.
    
    Args:
        project_id: Filter by project ID
        offset: Number of clips to skip
        limit: Maximum number of clips to return (1-100)
        db: Database session
        
    Returns:
        Paginated list of clips
    """
    conditions = []
    if project_id:
        conditions.append(Clip.project_id == project_id)
    
    total_stmt = select(func.count()).select_from(Clip)
    if conditions:
        total_stmt = total_stmt.where(*conditions)
    total = db.execute(total_stmt).scalar() or 0
    
    stmt = select(Clip)
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(Clip.created_at.desc()).offset(offset).limit(limit)
    
    result = db.execute(stmt)
    clips = result.scalars().all()
    
    return PaginatedResponse[ClipRead](
        items=[ClipRead.model_validate(clip) for clip in clips],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{clip_id}", response_model=ClipRead)
async def get_clip(
    clip_id: str,
    db: Session = Depends(get_db),
) -> ClipRead:
    """
    Get a specific clip by ID.
    
    Args:
        clip_id: Clip identifier
        db: Database session
        
    Returns:
        Clip details
        
    Raises:
        ResourceNotFoundError: If clip is not found
    """
    repository = ClipRepository(db)
    clip = repository.get(clip_id)
    
    if clip is None:
        raise ResourceNotFoundError("Clip", clip_id)
    
    return ClipRead.model_validate(clip)


__all__ = ["router"]
