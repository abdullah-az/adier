from __future__ import annotations

import asyncio
import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ...models.enums import ProcessingJobStatus
from ...workers.job_manager import ProcessingJobLifecycle

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/progress", tags=["progress"])


class ProgressMessage(BaseModel):
    """WebSocket message for job progress updates."""
    job_id: str
    status: ProcessingJobStatus
    progress: float | None = None
    message: str | None = None
    timestamp: str
    metadata: dict[str, object] | None = None


class ProgressSubscription(BaseModel):
    """Client subscription request."""
    job_id: str


class ProgressBroadcaster:
    """In-memory broadcaster for progress updates."""
    
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    
    async def subscribe(self, job_id: str, websocket: WebSocket) -> None:
        """Subscribe a WebSocket to progress updates for a specific job."""
        async with self._lock:
            if job_id not in self._connections:
                self._connections[job_id] = set()
            self._connections[job_id].add(websocket)
            logger.debug(f"WebSocket subscribed to job {job_id}")
    
    async def unsubscribe(self, job_id: str, websocket: WebSocket) -> None:
        """Unsubscribe a WebSocket from progress updates."""
        async with self._lock:
            if job_id in self._connections:
                self._connections[job_id].discard(websocket)
                if not self._connections[job_id]:
                    del self._connections[job_id]
                logger.debug(f"WebSocket unsubscribed from job {job_id}")
    
    async def broadcast(self, message: ProgressMessage) -> None:
        """Broadcast a progress message to all subscribed clients."""
        async with self._lock:
            job_id = message.job_id
            if job_id not in self._connections:
                return
            
            # Create a copy of connections to avoid modification during iteration
            connections = list(self._connections[job_id])
            message_json = message.model_dump_json()
            
            disconnected = []
            for websocket in connections:
                try:
                    await websocket.send_text(message_json)
                except Exception as exc:
                    logger.warning(f"Failed to send progress update to WebSocket: {exc}")
                    disconnected.append(websocket)
            
            # Clean up disconnected WebSockets
            for websocket in disconnected:
                await self.unsubscribe(job_id, websocket)
    
    async def cleanup_websocket(self, websocket: WebSocket) -> None:
        """Remove WebSocket from all subscriptions."""
        async with self._lock:
            for job_id, connections in list(self._connections.items()):
                if websocket in connections:
                    connections.discard(websocket)
                    if not connections:
                        del self._connections[job_id]


# Global broadcaster instance
broadcaster = ProgressBroadcaster()


@router.websocket("/ws/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str) -> None:
    """
    WebSocket endpoint for real-time job progress updates.
    
    Clients connect to receive progress updates for a specific job.
    The endpoint handles:
    - Subscription to job progress updates
    - Heartbeat/ping messages
    - Automatic cleanup on disconnect
    """
    await websocket.accept()
    
    # Verify job exists
    job = ProcessingJobLifecycle.get_job(job_id)
    if job is None:
        await websocket.send_text(json.dumps({
            "error": f"Job {job_id} not found",
            "type": "error"
        }))
        await websocket.close()
        return
    
    # Subscribe to progress updates
    await broadcaster.subscribe(job_id, websocket)
    
    # Send current job status
    from datetime import datetime, timezone
    current_message = ProgressMessage(
        job_id=job_id,
        status=job.status,
        progress=job.result_payload.get("progress") if job.result_payload else None,
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata=job.result_payload or None
    )
    await websocket.send_text(current_message.model_dump_json())
    
    logger.info(f"WebSocket client connected for job {job_id}")
    
    try:
        # Handle WebSocket communication
        while True:
            try:
                # Wait for message with timeout for heartbeat
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Parse client message
                try:
                    message = json.loads(data)
                    message_type = message.get("type")
                    
                    if message_type == "ping":
                        # Respond to ping with pong
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }))
                    elif message_type == "subscribe":
                        # Handle subscription to additional jobs
                        subscribe_job_id = message.get("job_id")
                        if subscribe_job_id and subscribe_job_id != job_id:
                            subscribe_job = ProcessingJobLifecycle.get_job(subscribe_job_id)
                            if subscribe_job:
                                await broadcaster.subscribe(subscribe_job_id, websocket)
                            else:
                                await websocket.send_text(json.dumps({
                                    "error": f"Job {subscribe_job_id} not found",
                                    "type": "error"
                                }))
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received from WebSocket: {data}")
                    await websocket.send_text(json.dumps({
                        "error": "Invalid JSON format",
                        "type": "error"
                    }))
                    
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }))
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from job {job_id}")
    except Exception as exc:
        logger.error(f"WebSocket error for job {job_id}: {exc}")
        await websocket.send_text(json.dumps({
            "error": "Internal server error",
            "type": "error"
        }))
    finally:
        # Clean up subscription
        await broadcaster.unsubscribe(job_id, websocket)
        await broadcaster.cleanup_websocket(websocket)


# Helper function to be called by job lifecycle updates
async def publish_job_progress(
    job_id: str,
    status: ProcessingJobStatus,
    progress: float | None = None,
    message: str | None = None,
    metadata: dict[str, object] | None = None,
) -> None:
    """Publish job progress to all subscribed WebSocket clients."""
    from datetime import datetime, timezone
    
    progress_message = ProgressMessage(
        job_id=job_id,
        status=status,
        progress=progress,
        message=message,
        timestamp=datetime.now(timezone.utc).isoformat(),
        metadata=metadata,
    )
    
    await broadcaster.broadcast(progress_message)


__all__ = [
    "router",
    "ProgressMessage",
    "ProgressSubscription",
    "ProgressBroadcaster",
    "publish_job_progress",
]