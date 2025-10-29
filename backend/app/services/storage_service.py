from __future__ import annotations

import hashlib
import shutil
import tempfile
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import BinaryIO, Optional

from ..core.config import Settings
from ..models.enums import MediaAssetType
from ..models.media_asset import MediaAsset
from ..repositories.media_asset import MediaAssetRepository
from ..utils.pathing import asset_relative_path, ensure_within_root, to_relative_path

_CHUNK_SIZE = 1024 * 1024  # 1 MiB


class StorageError(Exception):
    """Base class for storage related failures."""


class AssetNotFoundError(StorageError):
    def __init__(self, asset_id: str) -> None:
        super().__init__(f"Asset '{asset_id}' was not found")
        self.asset_id = asset_id


class AssetFileMissingError(StorageError):
    def __init__(self, asset_id: str, file_path: Path) -> None:
        super().__init__(f"Asset '{asset_id}' file missing at '{file_path}'")
        self.asset_id = asset_id
        self.file_path = file_path


class StorageQuotaExceeded(StorageError):
    def __init__(self, *, used_bytes: int, attempted_bytes: int, max_bytes: int) -> None:
        super().__init__(
            "Storage quota exceeded: attempted to store "
            f"{attempted_bytes} bytes with {used_bytes} bytes already used "
            f"(quota {max_bytes} bytes)"
        )
        self.used_bytes = used_bytes
        self.attempted_bytes = attempted_bytes
        self.max_bytes = max_bytes


class ChecksumMismatchError(StorageError):
    def __init__(self, *, expected: str, actual: str) -> None:
        super().__init__(f"Checksum mismatch: expected {expected} but calculated {actual}")
        self.expected = expected
        self.actual = actual


@dataclass(frozen=True)
class SignedPath:
    path: str
    expires_at: datetime
    checksum: Optional[str]
    size_bytes: Optional[int]
    mime_type: Optional[str]


@dataclass(frozen=True)
class StorageUsage:
    used_bytes: int
    max_bytes: Optional[int]
    available_bytes: Optional[int]


class StorageService:
    """File-system backed media asset storage service."""

    def __init__(self, settings: Settings, repository: MediaAssetRepository) -> None:
        self._settings = settings
        self._repository = repository

    def ingest_media_asset(
        self,
        *,
        project_id: str,
        asset_type: MediaAssetType,
        fileobj: BinaryIO,
        filename: str,
        mime_type: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        expected_checksum: Optional[str] = None,
    ) -> MediaAsset:
        asset_id = str(uuid.uuid4())
        relative_path = asset_relative_path(project_id, asset_type, asset_id, filename)
        destination_path = ensure_within_root(self._settings.storage_root, relative_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)

        checksum = hashlib.sha256()
        total_bytes = 0
        temp_path: Optional[Path] = None

        with tempfile.NamedTemporaryFile(dir=self._settings.storage_temp, delete=False) as temp_file:
            temp_path = Path(temp_file.name)
            while True:
                chunk = fileobj.read(_CHUNK_SIZE)
                if not chunk:
                    break
                if isinstance(chunk, str):
                    raise TypeError("File-like object must be opened in binary mode")
                temp_file.write(chunk)
                total_bytes += len(chunk)
                checksum.update(chunk)

        try:
            digest = checksum.hexdigest()
            if expected_checksum and digest != expected_checksum.lower():
                raise ChecksumMismatchError(expected=expected_checksum.lower(), actual=digest)

            usage = self.report_space_usage()
            if (
                self._settings.storage_max_bytes is not None
                and usage.used_bytes + total_bytes > self._settings.storage_max_bytes
            ):
                raise StorageQuotaExceeded(
                    used_bytes=usage.used_bytes,
                    attempted_bytes=total_bytes,
                    max_bytes=self._settings.storage_max_bytes,
                )

            shutil.move(str(temp_path), str(destination_path))

            stored_relative = to_relative_path(self._settings.storage_root, destination_path)
            stored_filename = destination_path.name

            asset_data = {
                "id": asset_id,
                "project_id": project_id,
                "type": asset_type,
                "filename": stored_filename,
                "file_path": stored_relative.as_posix(),
                "mime_type": mime_type,
                "size_bytes": total_bytes,
                "duration_seconds": duration_seconds,
                "checksum": digest,
            }
            return self._repository.create(asset_data)

        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def generate_signed_path(self, asset_id: str, *, expires_in: int = 300) -> SignedPath:
        asset = self._get_asset(asset_id)
        absolute_path = ensure_within_root(self._settings.storage_root, asset.file_path)
        expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return SignedPath(
            path=str(absolute_path),
            expires_at=expiry,
            checksum=asset.checksum,
            size_bytes=asset.size_bytes,
            mime_type=asset.mime_type,
        )

    def resolve_asset_path(self, asset_id: str) -> Path:
        asset = self._get_asset(asset_id)
        return ensure_within_root(self._settings.storage_root, asset.file_path)

    def delete_media_asset(self, asset_id: str) -> None:
        asset = self._get_asset(asset_id)
        file_path = ensure_within_root(self._settings.storage_root, asset.file_path)

        try:
            file_path.unlink()
        except FileNotFoundError as exc:
            self._repository.delete(asset)
            raise AssetFileMissingError(asset_id, file_path) from exc
        else:
            self._repository.delete(asset)
            self._prune_empty_directories(file_path.parent)

    def report_space_usage(self) -> StorageUsage:
        used_bytes = self._calculate_used_bytes(self._settings.storage_root)
        max_bytes = self._settings.storage_max_bytes
        available_bytes = None if max_bytes is None else max(max_bytes - used_bytes, 0)
        return StorageUsage(
            used_bytes=used_bytes,
            max_bytes=max_bytes,
            available_bytes=available_bytes,
        )

    def _get_asset(self, asset_id: str) -> MediaAsset:
        asset = self._repository.get(asset_id)
        if asset is None:
            raise AssetNotFoundError(asset_id)
        return asset

    @staticmethod
    def _calculate_used_bytes(root: Path) -> int:
        total = 0
        if not root.exists():
            return total
        for entry in root.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
        return total

    def _prune_empty_directories(self, start: Path) -> None:
        root = self._settings.storage_root.resolve()
        current = start.resolve()
        while current != root and root in current.parents:
            try:
                current.rmdir()
            except OSError:
                break
            current = current.parent.resolve()


__all__ = [
    "StorageService",
    "StorageError",
    "AssetNotFoundError",
    "AssetFileMissingError",
    "StorageQuotaExceeded",
    "ChecksumMismatchError",
    "SignedPath",
    "StorageUsage",
]
