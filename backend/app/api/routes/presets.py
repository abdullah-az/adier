from __future__ import annotations

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...core.errors import ResourceNotFoundError
from ...models.enums import PresetCategory
from ...models.preset import Preset
from ...repositories.preset import PresetRepository
from ...schemas.pagination import PaginatedResponse
from ...schemas.preset import PresetRead

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("/", response_model=PaginatedResponse[PresetRead])
async def list_presets(
    category: Annotated[Optional[PresetCategory], Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: Session = Depends(get_db),
) -> PaginatedResponse[PresetRead]:
    """
    List presets with optional category filtering.
    
    Args:
        category: Filter by preset category
        offset: Number of presets to skip
        limit: Maximum number of presets to return (1-100)
        db: Database session
        
    Returns:
        Paginated list of presets
    """
    conditions = []
    if category:
        conditions.append(Preset.category == category)
    
    total_stmt = select(func.count()).select_from(Preset)
    if conditions:
        total_stmt = total_stmt.where(*conditions)
    total = db.execute(total_stmt).scalar() or 0
    
    stmt = select(Preset)
    if conditions:
        stmt = stmt.where(*conditions)
    stmt = stmt.order_by(Preset.created_at.desc()).offset(offset).limit(limit)
    
    result = db.execute(stmt)
    presets = result.scalars().all()
    
    return PaginatedResponse[PresetRead](
        items=[PresetRead.model_validate(preset) for preset in presets],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{preset_id}", response_model=PresetRead)
async def get_preset(
    preset_id: str,
    db: Session = Depends(get_db),
) -> PresetRead:
    """
    Get a specific preset by ID.
    
    Args:
        preset_id: Preset identifier
        db: Database session
        
    Returns:
        Preset details
        
    Raises:
        ResourceNotFoundError: If preset is not found
    """
    repository = PresetRepository(db)
    preset = repository.get(preset_id)
    
    if preset is None:
        raise ResourceNotFoundError("Preset", preset_id)
    
    return PresetRead.model_validate(preset)


__all__ = ["router"]
