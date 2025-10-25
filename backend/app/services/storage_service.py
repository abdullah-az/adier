from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from loguru import logger

from app.models.video_asset import VideoAsset
from app.repositories.video_repository import VideoAssetRepository
from app.utils.ffmpeg import extract_thumbnail, get_video_metadata
from app.utils.storage import StorageManager


class StorageService:
    """Business logic for managing video storage and metadata."""

    def __init__(self, storage_manager: StorageManager, video_repository: VideoAssetRepository) -> None:
        self.storage_manager = storage_manager
        self.video_repository = video_repository

    async def upload_video(
        self,
        project_id: str,
        upload: UploadFile,
        generate_thumbnail: bool = True,
    ) -> VideoAsset:
        """
        Upload a video file, store it, and register metadata.
        
        Args:
            project_id: Project identifier
            upload: Uploaded file
            generate_thumbnail: Whether to generate thumbnail (default: True)
            
        Returns:
            Created VideoAsset with metadata
        """
        logger.info(
            "Processing video upload",
            project_id=project_id,
            filename=upload.filename,
        )

        # Stream upload to disk
        stored_file = await self.storage_manager.stream_upload(project_id, upload)

        # Create asset record
        asset = VideoAsset(
            id=str(uuid.uuid4()),
            project_id=project_id,
            filename=stored_file.filename,
            original_filename=stored_file.original_filename,
            relative_path=stored_file.relative_path,
            checksum=stored_file.checksum,
            size_bytes=stored_file.size_bytes,
            mime_type=stored_file.mime_type,
            status="uploaded",
            thumbnail_path=None,
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Persist to repository
        asset = await self.video_repository.add(asset)

        # Enqueue background processing for metadata and thumbnail
        # For now, we'll do it synchronously as a placeholder
        if generate_thumbnail:
            try:
                await self._generate_metadata_and_thumbnail(asset)
            except Exception as e:
                logger.error(
                    "Failed to generate metadata/thumbnail",
                    asset_id=asset.id,
                    error=str(e),
                )

        logger.info("Video upload completed", asset_id=asset.id, project_id=project_id)
        return asset

    def _build_metadata_stub(self, asset: VideoAsset) -> dict:
        """Build placeholder metadata when FFmpeg is unavailable."""
        return {
            "duration": 0.0,
            "width": 1920,
            "height": 1080,
            "codec": "unknown",
            "fps": 30.0,
            "bitrate": 0,
            "size_bytes": asset.size_bytes,
            "stub": True,
        }

    async def _generate_metadata_and_thumbnail(self, asset: VideoAsset) -> None:
        """
        Generate video metadata and thumbnail (stub for future implementation).
        
        Args:
            asset: Video asset to process
        """
        logger.info("Generating metadata and thumbnail", asset_id=asset.id)

        # Update status
        asset.status = "processing"
        await self.video_repository.update(asset)

        video_path = Path(self.storage_manager.storage_root) / asset.relative_path

        # Metadata extraction (stub-friendly)
        try:
            metadata = await get_video_metadata(video_path)
        except Exception as e:
            logger.warning(
                "FFmpeg metadata extraction unavailable; using stub metadata",
                asset_id=asset.id,
                error=str(e),
            )
            metadata = self._build_metadata_stub(asset)
        asset.metadata = metadata

        # Thumbnail generation (stub-friendly)
        thumbnail_path = self.storage_manager.build_thumbnail_path(
            asset.project_id,
            asset.filename,
        )
        try:
            await extract_thumbnail(video_path, thumbnail_path, timestamp=1.0)
            asset.thumbnail_path = str(thumbnail_path.relative_to(self.storage_manager.storage_root))
        except Exception as e:
            logger.warning(
                "Thumbnail generation skipped; creating placeholder",
                asset_id=asset.id,
                error=str(e),
            )
            placeholder_path = thumbnail_path.with_suffix(thumbnail_path.suffix + ".placeholder")
            placeholder_path.parent.mkdir(parents=True, exist_ok=True)
            placeholder_path.write_text("Thumbnail generation pending\n", encoding="utf-8")
            asset.thumbnail_path = str(placeholder_path.relative_to(self.storage_manager.storage_root))
            asset.metadata.setdefault("thumbnail", {})["placeholder"] = True

        asset.status = "ready"
        asset.updated_at = datetime.utcnow()
        await self.video_repository.update(asset)

    async def get_video_asset(self, asset_id: str) -> Optional[VideoAsset]:
        """Retrieve a video asset by ID."""
        return await self.video_repository.get(asset_id)

    async def list_project_videos(self, project_id: str) -> list[VideoAsset]:
        """List all video assets for a project."""
        return await self.video_repository.list_by_project(project_id)

    async def delete_video_asset(self, asset_id: str) -> bool:
        """
        Delete a video asset and its associated files.
        
        Args:
            asset_id: Asset identifier
            
        Returns:
            True if deleted successfully
        """
        asset = await self.video_repository.get(asset_id)
        if not asset:
            logger.warning("Asset not found for deletion", asset_id=asset_id)
            return False

        # Delete files from storage
        video_path = Path(self.storage_manager.storage_root) / asset.relative_path
        self.storage_manager.delete_file(video_path)

        if asset.thumbnail_path:
            thumbnail_path = Path(self.storage_manager.storage_root) / asset.thumbnail_path
            self.storage_manager.delete_file(thumbnail_path)

        # Delete metadata
        await self.video_repository.delete(asset_id)

        logger.info("Deleted video asset", asset_id=asset_id)
        return True

    async def delete_project_storage(self, project_id: str) -> None:
        """
        Delete all storage for a project.
        
        Args:
            project_id: Project identifier
        """
        logger.info("Deleting project storage", project_id=project_id)

        # Delete metadata records
        await self.video_repository.delete_for_project(project_id)

        # Clean up file storage
        self.storage_manager.cleanup_project(project_id)

        logger.info("Project storage deleted", project_id=project_id)

    def get_storage_stats(self, project_id: str | None = None) -> dict:
        """Get storage usage statistics."""
        if project_id is not None:
            return self.storage_manager.project_storage_usage(project_id)
        return self.storage_manager.storage_usage()
