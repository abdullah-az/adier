from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Path, Query
from loguru import logger

from app.schemas.timeline import (
    AISceneResponse,
    TimelineCreateRequest,
    TimelineResponse,
    TimelineUpdateRequest,
    TranscriptSearchRequest,
    TranscriptSearchResponse,
    TranscriptSegmentResponse,
)
from app.services.timeline_service import TimelineService

router = APIRouter(prefix="/projects/{project_id}/timelines", tags=["timelines"])


@router.post("", response_model=TimelineResponse, status_code=201)
async def create_timeline(
    project_id: str = Path(..., description="Project identifier"),
    request: TimelineCreateRequest = ...,
) -> TimelineResponse:
    """Create a new timeline for a project."""
    logger.info(f"Creating timeline for project {project_id}: {request.name}")
    
    try:
        timeline = await TimelineService.create_timeline(project_id, request)
        return timeline
    except Exception as e:
        logger.error(f"Failed to create timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[TimelineResponse])
async def list_timelines(
    project_id: str = Path(..., description="Project identifier"),
) -> list[TimelineResponse]:
    """List all timelines for a project."""
    logger.info(f"Listing timelines for project {project_id}")
    
    try:
        timelines = await TimelineService.list_timelines(project_id)
        return timelines
    except Exception as e:
        logger.error(f"Failed to list timelines: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{timeline_id}", response_model=TimelineResponse)
async def get_timeline(
    project_id: str = Path(..., description="Project identifier"),
    timeline_id: str = Path(..., description="Timeline identifier"),
) -> TimelineResponse:
    """Get a specific timeline."""
    logger.info(f"Getting timeline {timeline_id} for project {project_id}")
    
    try:
        timeline = await TimelineService.get_timeline(project_id, timeline_id)
        if not timeline:
            raise HTTPException(status_code=404, detail="Timeline not found")
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{timeline_id}", response_model=TimelineResponse)
async def update_timeline(
    project_id: str = Path(..., description="Project identifier"),
    timeline_id: str = Path(..., description="Timeline identifier"),
    request: TimelineUpdateRequest = ...,
) -> TimelineResponse:
    """Update a timeline with optimistic updates."""
    logger.info(f"Updating timeline {timeline_id} for project {project_id}")
    
    try:
        timeline = await TimelineService.update_timeline(project_id, timeline_id, request)
        if not timeline:
            raise HTTPException(status_code=404, detail="Timeline not found")
        return timeline
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{timeline_id}", status_code=204)
async def delete_timeline(
    project_id: str = Path(..., description="Project identifier"),
    timeline_id: str = Path(..., description="Timeline identifier"),
):
    """Delete a timeline."""
    logger.info(f"Deleting timeline {timeline_id} for project {project_id}")
    
    try:
        success = await TimelineService.delete_timeline(project_id, timeline_id)
        if not success:
            raise HTTPException(status_code=404, detail="Timeline not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/../ai-scenes", response_model=list[AISceneResponse])
async def get_ai_scenes(
    project_id: str = Path(..., description="Project identifier"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    min_quality: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum quality score"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence"),
) -> list[AISceneResponse]:
    """Get AI-detected scenes for a project."""
    logger.info(f"Getting AI scenes for project {project_id}")
    
    try:
        scenes = await TimelineService.get_ai_scenes(
            project_id, 
            asset_id=asset_id,
            min_quality=min_quality,
            min_confidence=min_confidence,
        )
        return scenes
    except Exception as e:
        logger.error(f"Failed to get AI scenes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/../transcript/search", response_model=TranscriptSearchResponse)
async def search_transcript(
    project_id: str = Path(..., description="Project identifier"),
    request: TranscriptSearchRequest = ...,
) -> TranscriptSearchResponse:
    """Search transcript for specific text and return matching segments."""
    logger.info(f"Searching transcript for project {project_id}: {request.query}")
    
    try:
        results = await TimelineService.search_transcript(project_id, request)
        return results
    except Exception as e:
        logger.error(f"Failed to search transcript: {e}")
        raise HTTPException(status_code=500, detail=str(e))
