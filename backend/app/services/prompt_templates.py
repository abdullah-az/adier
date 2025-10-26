from __future__ import annotations

from textwrap import dedent
from typing import Optional

from app.models.subtitle import SubtitleTranscript


def _format_timestamp(seconds: float) -> str:
    total_seconds = max(seconds, 0.0)
    minutes = int(total_seconds // 60)
    secs = int(total_seconds % 60)
    millis = int((total_seconds - int(total_seconds)) * 1000)
    return f"{minutes:02d}:{secs:02d}.{millis:03d}"


def build_transcript_excerpt(
    transcript: SubtitleTranscript,
    *,
    max_characters: int = 6000,
    max_segments: int = 200,
) -> str:
    """Return a condensed transcript excerpt suitable for prompting the LLM."""

    lines: list[str] = []
    total_chars = 0
    for segment in transcript.segments[:max_segments]:
        text = segment.text.strip()
        if not text:
            continue
        line = f"[{_format_timestamp(segment.start)}] {text}"
        lines.append(line)
        total_chars += len(line)
        if total_chars >= max_characters:
            break
    excerpt = "\n".join(lines)
    if not excerpt and transcript.text:
        excerpt = transcript.text[:max_characters]
    return excerpt


def build_scene_detection_messages(
    transcript: SubtitleTranscript,
    *,
    tone: Optional[str],
    highlight_criteria: Optional[str],
    max_scenes: int,
    extra_instructions: Optional[str] = None,
) -> list[dict[str, str]]:
    """Construct system + user messages for the scene detection analysis."""

    excerpt = build_transcript_excerpt(transcript)
    criteria = highlight_criteria or "Select the most compelling and emotionally resonant moments."
    tone_description = tone or "Inspiring and audience-friendly"

    system_prompt = dedent(
        """
        You are an expert video story editor. Analyse transcripts to find the most compelling, shareable scenes.
        Always respond with valid JSON that strictly follows the provided schema without additional commentary.
        Prefer scenes that have clear start and end timestamps and deliver a coherent story beat.
        """
    ).strip()

    instructions = dedent(
        f"""
        Use the provided transcript excerpt to identify up to {max_scenes} highlight scenes.
        For each scene include:
        - title: short editorial label
        - description: why this moment works, referencing the transcript
        - start/end: timestamps in seconds
        - confidence: 0.0 - 1.0 confidence score
        - tags: array of lowercase tags (e.g. ["call-to-action", "emotion"])
        - priority: 1 is highest priority, increment by 1 for subsequent scenes

        Additional guidance:
        - Desired tone: {tone_description}
        - Highlight selection criteria: {criteria}
        - Target clip duration: aim for concise scenes between 15 and 40 seconds unless the content requires longer.
        - Ensure scenes are non-overlapping and sequential.
        """
    ).strip()

    if extra_instructions:
        instructions += "\n" + extra_instructions.strip()

    instructions += dedent(
        """

        Respond with JSON following this schema:
        {
          "scenes": [
            {
              "title": "string",
              "description": "string",
              "start": 0.0,
              "end": 0.0,
              "confidence": 0.85,
              "tags": ["tag"],
              "priority": 1
            }
          ],
          "metadata": {
            "recommended_total_duration": 120,
            "notes": "string"
          }
        }
        """
    )

    user_prompt = dedent(
        f"""
        <transcript>
        {excerpt}
        </transcript>
        """
    ).strip()

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": instructions + "\n" + user_prompt},
    ]


__all__ = [
    "build_transcript_excerpt",
    "build_scene_detection_messages",
]
