from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.enums import ProcessingJobStatus, ProcessingJobType
from ...schemas.processing_job import ProcessingJobCreate, ProcessingJobRead
from ...workers.job_manager import ProcessingJobLifecycle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/", response_model=ProcessingJobRead, status_code=202)
async def create_and_enqueue_job(
    job_type: ProcessingJobType,
    payload: dict[str, object],
    clip_version_id: Optional[str] = None,
    priority: int = 0,
) -> ProcessingJobRead:
    """
    Create and enqueue a new background processing job.
    
    Args:
        job_type: Type of processing job (ingest, transcribe, etc.)
        payload: Job-specific configuration and parameters
        clip_version_id: Optional associated clip version ID
        priority: Job priority (higher values = higher priority)
        
    Returns:
        Created job with QUEUED status
        
    Raises:
        HTTPException: If job enqueueing fails due to queue connection issues
    """
    try:
        job = ProcessingJobLifecycle.enqueue(
            job_type=job_type,
            payload=payload,
            clip_version_id=clip_version_id,
            priority=priority,
        )
        
        return ProcessingJobRead.model_validate(job)
    
    except RuntimeError as exc:
        logger.error("Failed to enqueue job", extra={"error": str(exc)}, exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to enqueue job: {str(exc)}",
        ) from exc


@router.get("/{job_id}", response_model=ProcessingJobRead)
async def get_job_status(job_id: str) -> ProcessingJobRead:
    """
    Retrieve the status of a processing job.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Current job status and metadata
        
    Raises:
        HTTPException: If job is not found
    """
    job = ProcessingJobLifecycle.get_job(job_id)
    
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    return ProcessingJobRead.model_validate(job)


__all__ = ["router"]
