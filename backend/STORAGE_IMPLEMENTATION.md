# Storage Implementation Summary

## Overview

This document outlines the implementation of storage handling for video upload and management in the cto backend.

## Architecture

### Components

1. **StorageManager** (`app/utils/storage.py`)
   - Manages file storage operations
   - Creates and maintains storage directory structure
   - Handles chunked file uploads
   - Validates file types (MP4, MOV, AVI)
   - Generates deterministic filenames to prevent collisions
   - Provides cleanup utilities for project deletion

2. **VideoAssetRepository** (`app/repositories/video_repository.py`)
   - JSON-based persistence for video asset metadata
   - Thread-safe operations using asyncio locks
   - CRUD operations for video assets
   - Project-scoped queries and cleanup

3. **StorageService** (`app/services/storage_service.py`)
   - Business logic layer coordinating storage and metadata
   - Handles video upload workflow
   - Manages thumbnail generation (with FFmpeg stub support)
   - Extracts video metadata (with fallback stubs)
   - Orchestrates cleanup operations

4. **FFmpeg Utilities** (`app/utils/ffmpeg.py`)
   - Thumbnail extraction from videos
   - Video metadata extraction
   - Graceful error handling for missing FFmpeg

5. **API Endpoints** (`app/api/videos.py`, `app/api/storage.py`)
   - RESTful endpoints for video upload/management
   - Storage statistics endpoints
   - Project deletion with storage cleanup

## Storage Layout

```
storage/
├── uploads/          # Raw video uploads
│   └── project_{id}/
├── processed/        # Transcoded/optimized videos (future)
│   └── project_{id}/
├── thumbnails/       # Generated thumbnails
│   └── project_{id}/
├── exports/          # Final exports (future)
│   └── project_{id}/
├── music/            # Audio assets (future)
│   └── project_{id}/
└── metadata/         # JSON metadata registry
    └── video_assets.json
```

## Key Features

### Upload Flow

1. Client sends multipart/form-data with video file
2. Backend validates file extension (.mp4, .mov, .avi)
3. File is streamed to disk in 4MB chunks using `aiofiles`
4. SHA-256 checksum calculated during streaming
5. Deterministic filename generated (timestamp + hash)
6. VideoAsset record created with metadata
7. Background processing for thumbnail/metadata extraction

### Filename Generation

Format: `{stem}-{hash}{ext}`
- Stem: Sanitized original filename
- Hash: 10-char SHA1 digest of project_id:filename:timestamp
- Extension: Validated video extension

### Validation

- File extension must be .mp4, .mov, or .avi
- Filenames are sanitized (alphanumeric, dash, underscore, dot)
- Project IDs are sanitized for filesystem safety

### Cleanup

When a project is deleted:
1. All VideoAsset metadata records removed
2. All files in project directories deleted
3. Empty project directories removed across all categories

### Storage Statistics

Two endpoints provide visibility:
- `/storage/stats` - Global usage across all projects
- `/projects/{project_id}/storage/stats` - Project-specific usage

Each reports:
- File count per category
- Total bytes per category
- Megabytes per category

## Configuration

Environment variables in `.env`:

```bash
STORAGE_PATH=./storage          # Root storage directory
UPLOAD_MAX_SIZE=104857600       # 100MB upload limit
FFMPEG_THREADS=2                # FFmpeg parallelism
VIDEO_OUTPUT_FORMAT=mp4         # Default output format
```

## Testing

Test suite in `tests/test_storage_service.py` covers:
- Video upload and storage
- Project cleanup and verification
- Invalid file type rejection
- Metadata persistence

## FFmpeg Integration

The system gracefully handles missing FFmpeg:
- Thumbnail generation creates placeholder files
- Metadata extraction falls back to stub values
- Async execution using `asyncio.to_thread`

## Security Considerations

1. Filename sanitization prevents directory traversal
2. File type validation prevents arbitrary uploads
3. Checksums enable content verification
4. Storage directories excluded from git

## Future Enhancements

1. Video transcoding pipeline
2. Multiple resolution generation
3. Streaming video delivery
4. Cloud storage backends (S3, GCS)
5. Thumbnail sprite generation
6. Duplicate detection via checksum
7. Storage quota enforcement
8. Automatic cleanup of old assets

## Dependencies

- **aiofiles**: Async file I/O
- **fastapi**: Web framework
- **ffmpeg-python**: FFmpeg wrapper
- **loguru**: Structured logging
- **pydantic**: Data validation

## API Reference

### Upload Video
```
POST /projects/{project_id}/videos
Content-Type: multipart/form-data

Response:
{
  "asset_id": "uuid",
  "filename": "video-abc123.mp4",
  "original_filename": "lesson.mp4",
  "size_bytes": 1048576,
  "project_id": "demo",
  "status": "ready"
}
```

### List Project Videos
```
GET /projects/{project_id}/videos

Response:
[
  {
    "id": "uuid",
    "project_id": "demo",
    "filename": "video-abc123.mp4",
    "original_filename": "lesson.mp4",
    "relative_path": "uploads/demo/video-abc123.mp4",
    "checksum": "sha256hash",
    "size_bytes": 1048576,
    "mime_type": "video/mp4",
    "status": "ready",
    "thumbnail_path": "thumbnails/demo/video-abc123.jpg",
    "metadata": {...},
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

### Delete Video Asset
```
DELETE /projects/{project_id}/videos/{asset_id}
```

### Delete Project Storage
```
DELETE /projects/{project_id}/storage
```

### Storage Statistics
```
GET /storage/stats
GET /projects/{project_id}/storage/stats

Response:
{
  "root": "/path/to/storage",
  "categories": {
    "uploads": {
      "bytes": 1048576,
      "megabytes": 1.0,
      "file_count": 1
    },
    ...
  }
}
```

## Maintenance

### Monitoring Disk Usage

Check storage statistics regularly:
```bash
curl http://localhost:8000/storage/stats
```

### Manual Cleanup

If needed, directly clean storage:
```python
from app.utils.storage import StorageManager

manager = StorageManager("./storage")
manager.cleanup_project("project_id")
```

### Metadata Repair

If `video_assets.json` becomes corrupted, it can be rebuilt by scanning the storage directories and recreating metadata entries.
