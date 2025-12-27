import asyncio
import logging
from pathlib import Path
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class FFmpegService:
    def __init__(self):
        self.ffmpeg_path = settings.ffmpeg_path
        self.ffprobe_path = settings.ffprobe_path

    async def extract_audio_track(self, video_path: str, output_path: str) -> str:
        """
        Extract audio track from video file using FFmpeg.
        """
        video_file = Path(video_path)
        output_file = Path(output_path)
        
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_file),
            "-q:a", "0",
            "-map", "a",
            "-y",  # Overwrite output file if it exists
            str(output_file)
        ]
        
        logger.info(f"Extracting audio from {video_path} to {output_path}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"FFmpeg error: {error_msg}")
                raise Exception(f"FFmpeg failed with return code {process.returncode}: {error_msg}")
            
            if not output_file.exists():
                raise Exception("Output audio file was not created")
            
            logger.info(f"Successfully extracted audio to {output_path}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise

    async def get_video_info(self, video_path: str) -> dict:
        """
        Get video information using ffprobe.
        """
        video_file = Path(video_path)
        
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        cmd = [
            self.ffprobe_path,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_file)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                raise Exception(f"ffprobe failed with return code {process.returncode}: {error_msg}")
            
            import json
            return json.loads(stdout.decode())
            
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise

    async def add_subtitles_to_video(
        self, 
        video_path: str, 
        subtitles_path: str, 
        output_path: str,
        style: Optional[str] = None
    ) -> str:
        """
        Add subtitles to video using FFmpeg.
        """
        video_file = Path(video_path)
        subtitles_file = Path(subtitles_path)
        output_file = Path(output_path)
        
        if not video_file.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        if not subtitles_file.exists():
            raise FileNotFoundError(f"Subtitles file not found: {subtitles_path}")
        
        # Create output directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Define subtitle styling options
        if style == "karaoke":
            # Karaoke-style subtitle options
            subtitle_filter = "subtitles='{}':force_style='Name=Default,Fontsize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H40000000,Bold=1,Shadow=1,Alignment=2,Outline=1,BorderStyle=4,BackColour=&H80000000'".format(subtitles_path)
        else:
            # Default subtitle options
            subtitle_filter = f"subtitles='{subtitles_path}'"
        
        cmd = [
            self.ffmpeg_path,
            "-i", str(video_file),
            "-vf", subtitle_filter,
            "-c:a", "copy",
            "-y",  # Overwrite output file if it exists
            str(output_file)
        ]
        
        logger.info(f"Adding subtitles from {subtitles_path} to {video_path}, output to {output_path}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"FFmpeg error: {error_msg}")
                raise Exception(f"FFmpeg failed with return code {process.returncode}: {error_msg}")
            
            if not output_file.exists():
                raise Exception("Output video file with subtitles was not created")
            
            logger.info(f"Successfully added subtitles to video: {output_path}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error adding subtitles to video: {str(e)}")
            raise


# Create a global instance of FFmpegService
ffmpeg_service = FFmpegService()