import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from loguru import logger

from app.core.config import settings
from app.schemas.timeline import (
    AISceneResponse,
    TimelineCreateRequest,
    TimelineResponse,
    TimelineUpdateRequest,
    TranscriptSearchRequest,
    TranscriptSearchResponse,
    TranscriptSegmentResponse,
)


class TimelineService:
    """Service for managing timelines and AI suggestions."""

    @staticmethod
    def _get_timelines_file(project_id: str) -> Path:
        """Get the path to the timelines JSON file for a project."""
        metadata_dir = Path(settings.storage_root) / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        return metadata_dir / f"timelines_{project_id}.json"

    @staticmethod
    def _get_ai_scenes_file(project_id: str) -> Path:
        """Get the path to the AI scenes JSON file for a project."""
        metadata_dir = Path(settings.storage_root) / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        return metadata_dir / f"ai_scenes_{project_id}.json"

    @staticmethod
    def _get_transcripts_file(project_id: str) -> Path:
        """Get the path to the transcripts JSON file for a project."""
        metadata_dir = Path(settings.storage_root) / "metadata"
        metadata_dir.mkdir(parents=True, exist_ok=True)
        return metadata_dir / f"transcripts_{project_id}.json"

    @staticmethod
    async def create_timeline(
        project_id: str, request: TimelineCreateRequest
    ) -> TimelineResponse:
        """Create a new timeline."""
        timeline_id = str(uuid4())
        now = datetime.utcnow()

        timeline_data = {
            "id": timeline_id,
            "project_id": project_id,
            "name": request.name,
            "clips": [clip.model_dump() for clip in request.clips],
            "aspect_ratio": request.aspect_ratio,
            "resolution": request.resolution,
            "proxy_resolution": request.proxy_resolution,
            "background_music": request.background_music.model_dump() if request.background_music else None,
            "global_subtitles": request.global_subtitles.model_dump() if request.global_subtitles else None,
            "max_duration": request.max_duration,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        # Load existing timelines
        timelines_file = TimelineService._get_timelines_file(project_id)
        timelines = []
        if timelines_file.exists():
            with open(timelines_file, "r") as f:
                timelines = json.load(f)

        # Add new timeline
        timelines.append(timeline_data)

        # Save back to file
        with open(timelines_file, "w") as f:
            json.dump(timelines, f, indent=2)

        logger.info(f"Created timeline {timeline_id} for project {project_id}")
        return TimelineResponse(**timeline_data)

    @staticmethod
    async def list_timelines(project_id: str) -> list[TimelineResponse]:
        """List all timelines for a project."""
        timelines_file = TimelineService._get_timelines_file(project_id)
        
        if not timelines_file.exists():
            return []

        with open(timelines_file, "r") as f:
            timelines = json.load(f)

        return [TimelineResponse(**timeline) for timeline in timelines]

    @staticmethod
    async def get_timeline(
        project_id: str, timeline_id: str
    ) -> Optional[TimelineResponse]:
        """Get a specific timeline."""
        timelines_file = TimelineService._get_timelines_file(project_id)
        
        if not timelines_file.exists():
            return None

        with open(timelines_file, "r") as f:
            timelines = json.load(f)

        for timeline in timelines:
            if timeline["id"] == timeline_id:
                return TimelineResponse(**timeline)

        return None

    @staticmethod
    async def update_timeline(
        project_id: str, timeline_id: str, request: TimelineUpdateRequest
    ) -> Optional[TimelineResponse]:
        """Update a timeline."""
        timelines_file = TimelineService._get_timelines_file(project_id)
        
        if not timelines_file.exists():
            return None

        with open(timelines_file, "r") as f:
            timelines = json.load(f)

        # Find and update timeline
        updated = False
        for timeline in timelines:
            if timeline["id"] == timeline_id:
                # Update fields
                if request.name is not None:
                    timeline["name"] = request.name
                if request.clips is not None:
                    timeline["clips"] = [clip.model_dump() for clip in request.clips]
                if request.aspect_ratio is not None:
                    timeline["aspect_ratio"] = request.aspect_ratio
                if request.resolution is not None:
                    timeline["resolution"] = request.resolution
                if request.proxy_resolution is not None:
                    timeline["proxy_resolution"] = request.proxy_resolution
                if request.background_music is not None:
                    timeline["background_music"] = request.background_music.model_dump()
                if request.global_subtitles is not None:
                    timeline["global_subtitles"] = request.global_subtitles.model_dump()
                if request.max_duration is not None:
                    timeline["max_duration"] = request.max_duration
                
                timeline["updated_at"] = datetime.utcnow().isoformat()
                updated = True
                break

        if not updated:
            return None

        # Save back to file
        with open(timelines_file, "w") as f:
            json.dump(timelines, f, indent=2)

        logger.info(f"Updated timeline {timeline_id} for project {project_id}")
        
        # Return updated timeline
        for timeline in timelines:
            if timeline["id"] == timeline_id:
                return TimelineResponse(**timeline)

        return None

    @staticmethod
    async def delete_timeline(project_id: str, timeline_id: str) -> bool:
        """Delete a timeline."""
        timelines_file = TimelineService._get_timelines_file(project_id)
        
        if not timelines_file.exists():
            return False

        with open(timelines_file, "r") as f:
            timelines = json.load(f)

        # Filter out the timeline to delete
        original_count = len(timelines)
        timelines = [t for t in timelines if t["id"] != timeline_id]

        if len(timelines) == original_count:
            return False

        # Save back to file
        with open(timelines_file, "w") as f:
            json.dump(timelines, f, indent=2)

        logger.info(f"Deleted timeline {timeline_id} for project {project_id}")
        return True

    @staticmethod
    async def get_ai_scenes(
        project_id: str,
        asset_id: Optional[str] = None,
        min_quality: Optional[float] = None,
        min_confidence: Optional[float] = None,
    ) -> list[AISceneResponse]:
        """Get AI-detected scenes for a project."""
        scenes_file = TimelineService._get_ai_scenes_file(project_id)
        
        if not scenes_file.exists():
            # Return mock data for development
            return TimelineService._generate_mock_ai_scenes(project_id)

        with open(scenes_file, "r") as f:
            scenes = json.load(f)

        # Filter scenes
        filtered_scenes = scenes
        if asset_id:
            filtered_scenes = [s for s in filtered_scenes if s["asset_id"] == asset_id]
        if min_quality is not None:
            filtered_scenes = [s for s in filtered_scenes if s["quality_score"] >= min_quality]
        if min_confidence is not None:
            filtered_scenes = [s for s in filtered_scenes if s["confidence"] >= min_confidence]

        return [AISceneResponse(**scene) for scene in filtered_scenes]

    @staticmethod
    def _generate_mock_ai_scenes(project_id: str) -> list[AISceneResponse]:
        """Generate mock AI scenes for development."""
        mock_scenes = [
            {
                "id": str(uuid4()),
                "asset_id": "mock-asset-1",
                "start_time": 0.0,
                "end_time": 5.5,
                "confidence": 0.92,
                "quality_score": 0.88,
                "scene_type": "intro",
                "description": "Opening scene with title",
                "keywords": ["intro", "title", "opening"],
            },
            {
                "id": str(uuid4()),
                "asset_id": "mock-asset-1",
                "start_time": 5.5,
                "end_time": 15.2,
                "confidence": 0.85,
                "quality_score": 0.90,
                "scene_type": "content",
                "description": "Main content explanation",
                "keywords": ["explanation", "content", "main"],
            },
            {
                "id": str(uuid4()),
                "asset_id": "mock-asset-1",
                "start_time": 15.2,
                "end_time": 22.8,
                "confidence": 0.78,
                "quality_score": 0.75,
                "scene_type": "transition",
                "description": "Transition to next topic",
                "keywords": ["transition", "next"],
            },
            {
                "id": str(uuid4()),
                "asset_id": "mock-asset-1",
                "start_time": 22.8,
                "end_time": 35.0,
                "confidence": 0.95,
                "quality_score": 0.93,
                "scene_type": "highlight",
                "description": "Key highlight moment",
                "keywords": ["highlight", "important", "key"],
            },
            {
                "id": str(uuid4()),
                "asset_id": "mock-asset-1",
                "start_time": 35.0,
                "end_time": 42.5,
                "confidence": 0.88,
                "quality_score": 0.85,
                "scene_type": "outro",
                "description": "Closing remarks",
                "keywords": ["outro", "closing", "end"],
            },
        ]
        return [AISceneResponse(**scene) for scene in mock_scenes]

    @staticmethod
    async def search_transcript(
        project_id: str, request: TranscriptSearchRequest
    ) -> TranscriptSearchResponse:
        """Search transcript for matching segments."""
        transcripts_file = TimelineService._get_transcripts_file(project_id)
        
        if not transcripts_file.exists():
            # Return mock data for development
            return TimelineService._generate_mock_transcript_search(request.query)

        with open(transcripts_file, "r") as f:
            segments = json.load(f)

        # Search segments
        query_lower = request.query.lower()
        matching_segments = [
            s for s in segments
            if query_lower in s["text"].lower()
        ]

        # Filter by asset_ids if provided
        if request.asset_ids:
            matching_segments = [
                s for s in matching_segments
                if s["asset_id"] in request.asset_ids
            ]

        # Filter by duration if provided
        if request.min_duration is not None:
            matching_segments = [
                s for s in matching_segments
                if (s["end_time"] - s["start_time"]) >= request.min_duration
            ]
        if request.max_duration is not None:
            matching_segments = [
                s for s in matching_segments
                if (s["end_time"] - s["start_time"]) <= request.max_duration
            ]

        return TranscriptSearchResponse(
            segments=[TranscriptSegmentResponse(**seg) for seg in matching_segments],
            total_count=len(matching_segments),
        )

    @staticmethod
    def _generate_mock_transcript_search(query: str) -> TranscriptSearchResponse:
        """Generate mock transcript search results."""
        mock_segments = [
            {
                "id": str(uuid4()),
                "asset_id": "mock-asset-1",
                "start_time": 2.5,
                "end_time": 8.3,
                "text": f"This segment contains the keyword: {query}",
                "speaker": "Speaker 1",
                "confidence": 0.95,
            },
            {
                "id": str(uuid4()),
                "asset_id": "mock-asset-1",
                "start_time": 18.7,
                "end_time": 24.1,
                "text": f"Another mention of {query} in this section",
                "speaker": "Speaker 2",
                "confidence": 0.88,
            },
        ]
        return TranscriptSearchResponse(
            segments=[TranscriptSegmentResponse(**seg) for seg in mock_segments],
            total_count=len(mock_segments),
        )
