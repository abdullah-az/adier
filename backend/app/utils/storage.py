from __future__ import annotations

import hashlib
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import UploadFile
from loguru import logger


DEFAULT_CATEGORIES = ["uploads", "processed", "thumbnails", "exports", "music"]
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi"}
CHUNK_SIZE = 4 * 1024 * 1024  # 4MB chunks for streaming writes

_filename_sanitize_regex = re.compile(r"[^a-zA-Z0-9._-]+")


@dataclass
class StoredFile:
    """Metadata captured for a stored file."""

    filename: str
    original_filename: str
    absolute_path: Path
    relative_path: str
    size_bytes: int
    checksum: str
    mime_type: str
    category: str
    project_id: str


class StorageManager:
    """Utility responsible for organizing and interacting with the storage layout."""

    def __init__(self, storage_root: Path | str, categories: Optional[list[str]] = None) -> None:
        self.storage_root = Path(storage_root).resolve()
        self.categories = categories or list(DEFAULT_CATEGORIES)
        self._ensure_layout()

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------
    def _ensure_layout(self) -> None:
        """Ensure storage root and category directories exist."""
        self.storage_root.mkdir(parents=True, exist_ok=True)
        for category in self.categories:
            (self.storage_root / category).mkdir(parents=True, exist_ok=True)
            logger.debug("Ensured storage category exists", category=category)

    def ensure_project_directories(self, project_id: str) -> None:
        """Ensure per-project directories exist for all categories."""
        for category in self.categories:
            self._category_project_path(project_id, category).mkdir(parents=True, exist_ok=True)
        logger.debug("Ensured project storage directories", project_id=project_id)

    def _category_project_path(self, project_id: str, category: str) -> Path:
        if category not in self.categories:
            raise ValueError(f"Unknown storage category '{category}'")
        safe_project = self._sanitize_component(str(project_id))
        return self.storage_root / category / safe_project

    def project_category_path(self, project_id: str, category: str) -> Path:
        """Public helper returning the absolute path for a project's storage category."""
        return self._category_project_path(project_id, category)

    def _sanitize_component(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Storage path component cannot be empty")
        sanitized = _filename_sanitize_regex.sub("-", value)
        return sanitized.lower()

    # ------------------------------------------------------------------
    # File naming
    # ------------------------------------------------------------------
    def _generate_filename(self, project_id: str, original_filename: str) -> str:
        stem, ext = self._split_filename(original_filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        digest_source = f"{project_id}:{original_filename}:{timestamp}".encode()
        digest = hashlib.sha1(digest_source).hexdigest()[:10]
        filename = f"{stem}-{digest}{ext}"
        logger.debug("Generated deterministic filename", filename=filename)
        return filename

    def _split_filename(self, filename: str) -> tuple[str, str]:
        name = Path(filename).name or "video"
        ext = name[name.rfind("."):].lower() if "." in name else ""
        stem = name[: name.rfind(".")] if ext else name
        if not stem:
            stem = "video"
        stem = self._sanitize_component(stem)
        if not ext:
            ext = ".mp4"
        return stem, ext

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------
    def validate_video_file(self, filename: str) -> None:
        """Raise ValueError if filename does not match allowed extensions."""
        _, ext = self._split_filename(filename)
        if ext.lower() not in ALLOWED_VIDEO_EXTENSIONS:
            raise ValueError(
                f"Unsupported video format '{ext}'. Allowed formats: {', '.join(sorted(ALLOWED_VIDEO_EXTENSIONS))}"
            )

    # ------------------------------------------------------------------
    # Storage operations
    # ------------------------------------------------------------------
    async def stream_upload(
        self,
        project_id: str,
        upload: UploadFile,
        category: str = "uploads",
        chunk_size: int = CHUNK_SIZE,
    ) -> StoredFile:
        """Stream an incoming UploadFile to disk and capture metadata."""
        self.validate_video_file(upload.filename or "")
        self.ensure_project_directories(project_id)

        filename = self._generate_filename(project_id, upload.filename or "video")
        project_dir = self._category_project_path(project_id, category)
        destination = project_dir / filename

        size_bytes = 0
        digest = hashlib.sha256()

        logger.info(
            "Streaming upload to storage",
            project_id=project_id,
            destination=str(destination),
            original_filename=upload.filename,
        )

        async with aiofiles.open(destination, "wb") as buffer:
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break
                size_bytes += len(chunk)
                digest.update(chunk)
                await buffer.write(chunk)

        await upload.close()

        checksum = digest.hexdigest()
        relative_path = str(destination.relative_to(self.storage_root))

        logger.info(
            "Completed streaming upload",
            project_id=project_id,
            bytes=size_bytes,
            checksum=checksum,
            path=relative_path,
        )

        return StoredFile(
            filename=filename,
            original_filename=upload.filename or filename,
            absolute_path=destination,
            relative_path=relative_path,
            size_bytes=size_bytes,
            checksum=checksum,
            mime_type=upload.content_type or "application/octet-stream",
            category=category,
            project_id=str(project_id),
        )

    def build_thumbnail_path(self, project_id: str, filename: str, extension: str = ".jpg") -> Path:
        """Return where thumbnails should be saved for an asset."""
        stem, _ = self._split_filename(filename)
        thumbnail_name = f"{stem}.jpg" if not extension.startswith(".") else f"{stem}{extension}"
        return self._category_project_path(project_id, "thumbnails") / thumbnail_name

    def delete_file(self, path: Path) -> None:
        if path.exists():
            path.unlink()
            logger.info("Deleted file", path=str(path))
        else:
            logger.debug("Requested deletion for missing file", path=str(path))

    def cleanup_project(self, project_id: str) -> None:
        """Remove all category directories for a project."""
        for category in self.categories:
            project_dir = self._category_project_path(project_id, category)
            if project_dir.exists():
                shutil.rmtree(project_dir)
                logger.info("Removed project storage directory", path=str(project_dir))

    def storage_usage(self) -> dict:
        """Calculate disk usage for the storage root."""
        usage = {"root": str(self.storage_root), "categories": {}}
        for category in self.categories:
            category_dir = self.storage_root / category
            usage["categories"][category] = self._directory_stats(category_dir)
        return usage

    def project_storage_usage(self, project_id: str) -> dict:
        """Calculate disk usage for a specific project across categories."""
        usage = {"project_id": str(project_id), "categories": {}}
        for category in self.categories:
            project_dir = self._category_project_path(project_id, category)
            usage["categories"][category] = self._directory_stats(project_dir)
        return usage

    def _directory_stats(self, directory: Path) -> dict:
        total_bytes = sum(file.stat().st_size for file in directory.rglob("*") if file.is_file())
        file_count = sum(1 for file in directory.rglob("*") if file.is_file())
        return {
            "bytes": total_bytes,
            "megabytes": round(total_bytes / (1024 * 1024), 2),
            "file_count": file_count,
        }
