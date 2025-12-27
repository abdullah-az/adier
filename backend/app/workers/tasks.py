import asyncio
import logging
from typing import Any, Dict
from pathlib import Path

from app.core.config import settings
from app.services.analysis_service import AnalysisService
from app.services.ffmpeg_service import ffmpeg_service
from app.repositories.media_asset_repository import MediaAssetRepository
from app.schemas.job import JobStatus
from app.exceptions.analysis_service import AnalysisServiceError

logger = logging.getLogger(__name__)


async def _process_transcribe(job_id: str, media_asset_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process transcription task using real AI analysis instead of mock data.
    """
    try:
        # Inject AnalysisService and MediaAssetRepository
        analysis_service = AnalysisService()
        media_asset_repo = MediaAssetRepository()
        
        # Fetch the real asset using media_asset_id
        media_asset = await media_asset_repo.get_by_id(media_asset_id)
        if not media_asset:
            raise AnalysisServiceError(f"Media asset with ID {media_asset_id} not found")
        
        # Use ffmpeg_service.extract_audio_track to extract audio from video
        video_path = Path(media_asset.file_path)
        audio_path = video_path.with_suffix('.wav')
        
        await ffmpeg_service.extract_audio_track(str(video_path), str(audio_path))
        
        # Use analysis_service to send audio to OpenAI Whisper for real transcript
        transcript_result = await analysis_service.transcribe_audio(
            audio_file_path=str(audio_path),
            context=context.get('text_prompt', ''),
            language='ar'
        )
        
        # Store the result in database and update job status
        # This would typically involve updating the media_asset with transcription data
        await media_asset_repo.update_transcription(media_asset_id, transcript_result)
        
        # Update job status to completed
        # In a real implementation, you would update the job in your job queue system
        logger.info(f"Transcription completed for media asset {media_asset_id}")
        
        # Clean up temporary audio file
        if audio_path.exists():
            audio_path.unlink()
        
        return {
            'status': 'completed',
            'transcript': transcript_result,
            'media_asset_id': media_asset_id,
            'job_id': job_id
        }
        
    except AnalysisServiceError as e:
        logger.error(f"Analysis service error in transcription: {str(e)}")
        # Update job status to failed
        raise
    except Exception as e:
        logger.error(f"Unexpected error in transcription: {str(e)}")
        raise AnalysisServiceError(f"Transcription failed: {str(e)}")


async def _process_generate_clip(job_id: str, media_asset_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process clip generation using real AI analysis instead of mock data.
    """
    try:
        # Inject AnalysisService and MediaAssetRepository
        analysis_service = AnalysisService()
        media_asset_repo = MediaAssetRepository()
        
        # Fetch the real asset using media_asset_id
        media_asset = await media_asset_repo.get_by_id(media_asset_id)
        if not media_asset:
            raise AnalysisServiceError(f"Media asset with ID {media_asset_id} not found")
        
        # Use analysis_service.analyse_media_asset to analyze text and image
        analysis_result = await analysis_service.analyse_media_asset(
            media_asset_id=media_asset_id,
            context=context.get('text_prompt', '')
        )
        
        # Request AI (via the existing router) to suggest clips based on highlights and sentiment
        clip_suggestions = await analysis_service.generate_clip_suggestions(
            analysis_result=analysis_result,
            context=context
        )
        
        # Store the result in database and update job status
        await media_asset_repo.update_clip_suggestions(media_asset_id, clip_suggestions)
        
        # Update job status to completed
        logger.info(f"Clip generation completed for media asset {media_asset_id}")
        
        return {
            'status': 'completed',
            'clips': clip_suggestions,
            'media_asset_id': media_asset_id,
            'job_id': job_id
        }
        
    except AnalysisServiceError as e:
        logger.error(f"Analysis service error in clip generation: {str(e)}")
        # Update job status to failed
        raise
    except Exception as e:
        logger.error(f"Unexpected error in clip generation: {str(e)}")
        raise AnalysisServiceError(f"Clip generation failed: {str(e)}")


async def process_job(job_type: str, job_id: str, media_asset_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main job processing function that routes to appropriate task processors.
    """
    if job_type == 'transcribe':
        return await _process_transcribe(job_id, media_asset_id, context)
    elif job_type == 'generate_clip':
        return await _process_generate_clip(job_id, media_asset_id, context)
    else:
        raise ValueError(f"Unsupported job type: {job_type}")