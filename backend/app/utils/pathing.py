from __future__ import annotations

import re
from pathlib import Path

from ..models.enums import MediaAssetType

_COMPONENT_PATTERN = re.compile(r"[^a-z0-9_-]+")
_ALLOWED_FILENAME_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789-_.")


def normalise_component(value: str) -> str:
    """Normalise a string so it is safe for use as a path component."""

    cleaned = _COMPONENT_PATTERN.sub("-", value.strip().lower())
    cleaned = cleaned.strip("-_")
    return cleaned or "default"


def sanitise_filename(filename: str) -> str:
    """Normalise a filename while preserving dotted suffixes."""

    name = Path(filename).name
    stem = normalise_component(Path(name).stem)
    suffix = "".join(Path(name).suffixes)

    # Preserve characters that are known to be safe while replacing the rest
    safe_stem = "".join(c if c in _ALLOWED_FILENAME_CHARS else "-" for c in stem)
    safe_stem = safe_stem.strip("-_") or "asset"

    return f"{safe_stem}{suffix.lower()}"


def project_subdir(project_id: str) -> Path:
    return Path(normalise_component(project_id))


def asset_directory(project_id: str, asset_type: MediaAssetType, asset_id: str) -> Path:
    return project_subdir(project_id) / asset_type.value / normalise_component(asset_id)


def asset_relative_path(
    project_id: str, asset_type: MediaAssetType, asset_id: str, filename: str
) -> Path:
    return asset_directory(project_id, asset_type, asset_id) / sanitise_filename(filename)


def ensure_within_root(root: Path, relative_path: Path | str) -> Path:
    """Resolve a relative path under the provided root, guarding against escapes."""

    root = root.resolve()
    candidate = (root / Path(relative_path)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError("Resolved path escapes the storage root") from exc
    return candidate


def to_relative_path(root: Path, absolute_path: Path) -> Path:
    """Return a relative path beneath the root for the given absolute path."""

    absolute_path = absolute_path.resolve()
    root = root.resolve()
    try:
        return absolute_path.relative_to(root)
    except ValueError as exc:  # pragma: no cover - defensive guard
        raise ValueError("Path is not located within the storage root") from exc


__all__ = [
    "normalise_component",
    "sanitise_filename",
    "project_subdir",
    "asset_directory",
    "asset_relative_path",
    "ensure_within_root",
    "to_relative_path",
]
