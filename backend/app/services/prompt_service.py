from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger


_DEFAULT_SCENE_PROMPT: Dict[str, Any] = {
    "version": "v1",
    "tone": "insightful and energetic",
    "max_scenes": 5,
    "highlight_criteria": [
        "Clearly communicates a core concept or milestone",
        "Presents a surprising insight or compelling data point",
        "Pairs narration with visually distinctive moments",
        "Contains actionable steps or memorable advice",
    ],
    "system": (
        "You are an experienced video editor and story producer. "
        "Given a transcript, you identify the strongest highlight scenes, summarise them, "
        "and score how compelling they will be for a social media teaser."
    ),
    "user_template": (
        "Tone for recommendations: {tone}\n"
        "Highlight criteria (consider each bullet):\n{highlight_criteria}\n\n"
        "Provide up to {max_scenes} scenes ordered by highest impact. "
        "Respond as a JSON object with keys 'summary' (string) and 'scenes' (array).\n"
        "Each scene must include: index (int), title (string), description (string), start_seconds (float), "
        "end_seconds (float), highlight_score (0-1), confidence (0-1), tags (array of strings), "
        "recommended_duration (float).\n\n"
        "Transcript segments:\n{transcript}\n"
    ),
}


class PromptService:
    """Manage configurable prompt templates for AI services."""

    def __init__(self, config_path: Optional[str | Path] = None) -> None:
        self.config_path = Path(config_path).resolve() if config_path else None
        self._config: Dict[str, Any] = {}
        self._load_config()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_config(self) -> None:
        if not self.config_path:
            self._config = {}
            return

        if not self.config_path.exists():
            logger.debug("Prompt configuration file not found", path=str(self.config_path))
            self._config = {}
            return

        try:
            with self.config_path.open("r", encoding="utf-8") as handle:
                self._config = json.load(handle)
            logger.info("Loaded prompt configuration", path=str(self.config_path))
        except json.JSONDecodeError as exc:  # pragma: no cover - configuration issue
            logger.warning("Failed to parse prompt configuration", error=str(exc))
            self._config = {}
        except Exception as exc:  # pragma: no cover - unexpected
            logger.warning("Unable to load prompt configuration", error=str(exc))
            self._config = {}

    def reload(self) -> None:
        """Reload configuration from disk."""
        self._load_config()

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------
    def build_scene_detection_prompt(
        self,
        transcript_excerpt: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, str, Dict[str, Any]]:
        """Return the system prompt, user prompt, and metadata for scene detection."""
        config = deepcopy(_DEFAULT_SCENE_PROMPT)
        file_config = deepcopy(self._config.get("scene_detection", {})) if self._config else {}

        # Merge prioritising overrides > file > defaults
        for source in (file_config, overrides or {}):
            if not source:
                continue
            for key, value in source.items():
                if value is None:
                    continue
                config[key] = value

        highlight_criteria = config.get("highlight_criteria", [])
        if isinstance(highlight_criteria, list):
            highlight_text = "\n".join(f"- {item}" for item in highlight_criteria)
        else:
            highlight_text = str(highlight_criteria)

        metadata = {
            "version": config.get("version", "v1"),
            "tone": config.get("tone"),
            "max_scenes": config.get("max_scenes", _DEFAULT_SCENE_PROMPT["max_scenes"]),
            "highlight_criteria": highlight_criteria,
        }

        user_template = config.get("user_template", _DEFAULT_SCENE_PROMPT["user_template"])
        user_prompt = user_template.format(
            tone=config.get("tone", _DEFAULT_SCENE_PROMPT["tone"]),
            highlight_criteria=highlight_text,
            max_scenes=metadata["max_scenes"],
            transcript=transcript_excerpt.strip(),
        )

        system_prompt = config.get("system", _DEFAULT_SCENE_PROMPT["system"])
        return system_prompt, user_prompt, metadata

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    @property
    def raw_config(self) -> Dict[str, Any]:
        return deepcopy(self._config)
