from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from app.models.scene import SceneAnalysis, SceneDetection


class SceneDetectionResponse(BaseModel):
    id: str
    index: int
    title: str
    description: str
    start_seconds: float
    end_seconds: float
    start_timecode: str
    end_timecode: str
    highlight_score: float
    confidence: float
    tags: List[str] = Field(default_factory=list)
    recommended_duration: Optional[float] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_model(cls, scene: SceneDetection) -> "SceneDetectionResponse":
        return cls(**scene.model_dump())


class SceneAnalysisResponse(BaseModel):
    analysis_id: str = Field(alias="id")
    project_id: str
    asset_id: str
    model: str
    summary: Optional[str] = None
    scene_count: int
    scenes: List[SceneDetectionResponse]
    prompt: dict[str, Any] = Field(default_factory=dict)
    usage: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, analysis: SceneAnalysis) -> "SceneAnalysisResponse":
        scenes = [SceneDetectionResponse.from_model(scene) for scene in analysis.scenes]
        return cls(
            id=analysis.id,
            project_id=analysis.project_id,
            asset_id=analysis.asset_id,
            model=analysis.model,
            summary=analysis.summary,
            scene_count=len(scenes),
            scenes=scenes,
            prompt=analysis.prompt,
            usage=analysis.usage,
            metadata=analysis.metadata,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
        )


class SceneAnalysisListResponse(BaseModel):
    analyses: List[SceneAnalysisResponse]
