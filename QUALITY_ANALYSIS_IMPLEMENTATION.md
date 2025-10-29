# Quality Analysis Service Implementation

## Overview
This implementation provides automated visual and audio quality scoring to select the best video clips. The system computes metrics like sharpness, exposure, motion blur, and noise levels for each clip, stores them in the database, and provides ranking/retake suggestion capabilities.

## Components Implemented

### 1. Database Schema
**File**: `backend/alembic/versions/20241230_0002_add_quality_metrics.py`
- Added `quality_metrics` JSON column to `clip_versions` table
- Stores all quality metric scores in a flexible JSON structure

**Model Update**: `backend/app/models/clip.py`
- Added `quality_metrics` field to `ClipVersion` model
- Type: `Optional[Dict[str, Any]]` mapped to JSON column

### 2. Quality Service
**File**: `backend/app/services/video/quality_service.py`

Provides comprehensive video quality analysis:
- **Sharpness**: Uses Laplacian variance to measure focus and detail
- **Exposure**: Analyzes brightness levels and deviation from ideal
- **Motion Blur**: Detects blur artifacts from camera or subject movement
- **Noise Level**: Estimates sensor noise and graininess
- **Audio Quality**: Analyzes audio RMS levels and spectral clarity

**Features**:
- All scores normalized to 0-1 range
- Configurable sample count for frame analysis
- Configurable weighting system for overall score
- Handles videos with or without audio tracks
- Uses OpenCV for video analysis and librosa for audio analysis

**Classes**:
- `QualityService`: Main service class for quality analysis
- `QualityMetrics`: Data class holding all quality scores
- `QualityWeights`: Configurable weights for combining metrics
- `QualityAnalysisError`: Custom exception for analysis failures

### 3. Ranking Service
**File**: `backend/app/services/video/ranking_service.py`

Combines quality metrics with AI scores for intelligent ranking:

**Features**:
- Ranks clips by combined quality and AI scores
- Configurable weighting between quality and AI analysis
- Retrieves top-N clips
- Identifies clips requiring retakes
- Generates human-readable recommendations

**Classes**:
- `RankingService`: Main ranking orchestration
- `ClipRanking`: Data model for ranked clip results
- `RetakeSuggestion`: Data model for retake recommendations
- `RankingWeights`: Configurable weights for combining quality and AI scores

### 4. Repository Extensions
**File**: `backend/app/repositories/clip.py`

Added methods to `ClipVersionRepository`:
- `update_quality_metrics(version, metrics)`: Store quality metrics in DB
- `get_versions_by_quality_threshold(project_id, threshold)`: Query clips by quality score

### 5. Dependencies
**File**: `backend/requirements.txt`

Added:
- `opencv-python-headless`: Video analysis
- `numpy`: Numerical computations
- `librosa`: Audio analysis
- `soundfile`: Audio file I/O

## Usage Examples

### Analyze Video Quality
```python
from backend.app.services.video import QualityService, QualityWeights
from backend.app.services.video import FFmpegService
from backend.app.core.config import get_settings

settings = get_settings()
ffmpeg_service = FFmpegService(settings)
quality_service = QualityService(settings, ffmpeg_service)

# Analyze video
metrics = quality_service.analyse_video_quality(
    Path("/path/to/video.mp4"),
    sample_count=10
)

print(f"Sharpness: {metrics.sharpness:.2f}")
print(f"Exposure: {metrics.exposure:.2f}")
print(f"Motion Blur: {metrics.motion_blur:.2f}")
print(f"Noise Level: {metrics.noise_level:.2f}")
print(f"Audio Quality: {metrics.audio_quality:.2f}")
print(f"Overall Score: {metrics.overall_score:.2f}")
```

### Rank Clips
```python
from backend.app.services.video import RankingService, RankingWeights
from backend.app.repositories.clip import ClipVersionRepository

repository = ClipVersionRepository(db_session)
ranking_service = RankingService(
    repository,
    weights=RankingWeights(quality=0.6, ai_score=0.4)
)

# Get top 5 clips
top_clips = ranking_service.get_top_clips(
    clip_versions,
    top_n=5,
    scene_scores=ai_scene_scores
)

for clip in top_clips:
    print(f"Clip {clip.clip_version_id}: {clip.combined_score:.2f}")
    print(f"  Quality: {clip.quality_score:.2f}, AI: {clip.ai_score:.2f}")
    print(f"  Recommendation: {clip.recommendation}")
```

### Suggest Retakes
```python
# Find clips that need retakes
suggestions = ranking_service.suggest_retakes(
    clip_versions,
    quality_threshold=0.6
)

for suggestion in suggestions:
    print(f"\nClip {suggestion.clip_version_id} needs retake:")
    print(f"  Quality Score: {suggestion.quality_score:.2f}")
    print("  Issues:")
    for issue in suggestion.issues:
        print(f"    - {issue}")
```

### Store Metrics in Database
```python
from backend.app.repositories.clip import ClipVersionRepository

repository = ClipVersionRepository(db_session)

# Store quality metrics
repository.update_quality_metrics(clip_version, metrics.to_dict())

# Query high-quality clips
high_quality = repository.get_versions_by_quality_threshold(
    project_id="project-123",
    threshold=0.7
)
```

## Test Coverage

### Unit Tests
**File**: `backend/tests/test_ranking_service.py` (11 tests, all passing)
- Ranking order verification
- Quality and AI score combination
- Top-N selection
- Retake suggestions
- Weight normalization
- Missing metrics handling

**File**: `backend/tests/test_clip_repository.py` (4 tests, all passing)
- Quality metrics persistence
- Metric updates
- Threshold-based queries

### Integration Tests
**File**: `backend/tests/test_quality_service.py` (7 tests)
- Score normalization validation
- Consistency across runs
- Custom weight configuration
- Error handling
- Metric conversion

**Note**: Quality service tests require FFmpeg and sample video files. Tests are marked with `@pytest.mark.slow` and will skip if FFmpeg is not available.

## Quality Metrics Explained

### Sharpness (0-1)
- Higher = sharper image
- Uses Laplacian variance
- Threshold normalized to ~1000

### Exposure (0-1)
- Higher = better exposure
- Measures deviation from ideal brightness (128)
- 1.0 = perfect exposure

### Motion Blur (0-1)
- Higher = more blur (inverted in scoring)
- Uses frame-to-frame variance
- Combined with overall score as `(1.0 - motion_blur)`

### Noise Level (0-1)
- Higher = less noise
- Estimates sensor noise in center region
- Normalized to typical noise range

### Audio Quality (0-1, optional)
- Higher = better audio
- Combines RMS level (60%) and spectral clarity (40%)
- May be None if video has no audio

### Overall Score (0-1)
- Weighted combination of all metrics
- Default weights: sharpness (30%), exposure (20%), motion_blur (20%), noise (15%), audio (15%)
- Fully configurable via `QualityWeights`

## Acceptance Criteria Status

✅ **Quality assessment runs on sample media producing normalized scores between 0-1**
- All metrics normalized to 0-1 range
- Tested with various configurations

✅ **Ranked outputs align with expected ordering in tests**
- 11 ranking tests verify correct ordering
- Higher quality scores produce higher rankings
- Weights correctly influence final rankings

✅ **Metrics persisted to DB and retrievable via repository queries**
- 4 repository tests verify persistence
- JSON storage in `clip_versions.quality_metrics`
- Query by threshold functionality implemented

## Configuration

### Quality Analysis Weights
```python
QualityWeights(
    sharpness=0.3,      # Focus and detail
    exposure=0.2,       # Brightness
    motion_blur=0.2,    # Movement artifacts
    noise_level=0.15,   # Sensor noise
    audio_quality=0.15  # Audio clarity
)
```

### Ranking Weights
```python
RankingWeights(
    quality=0.5,   # Technical quality metrics
    ai_score=0.5   # AI-based scene scoring
)
```

## Future Enhancements

1. **GPU Acceleration**: Use CUDA for faster OpenCV operations
2. **Batch Processing**: Analyze multiple clips in parallel
3. **ML-based Quality**: Train model for perceptual quality assessment
4. **Real-time Analysis**: Stream processing for live feedback
5. **Custom Metrics**: Plugin system for domain-specific quality checks
6. **Comparative Analysis**: Benchmark against reference clips
7. **Temporal Consistency**: Analyze quality trends across clip segments
