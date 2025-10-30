from __future__ import annotations

import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence

import cv2
import librosa
import numpy as np
import soundfile as sf

from ...core.config import Settings
from .ffmpeg_service import FFmpegService


@dataclass(frozen=True)
class QualityMetrics:
    sharpness: float
    exposure: float
    motion_blur: float
    noise_level: float
    audio_quality: float | None
    overall_score: float

    def to_dict(self) -> Dict[str, float | None]:
        return {
            "sharpness": self.sharpness,
            "exposure": self.exposure,
            "motion_blur": self.motion_blur,
            "noise_level": self.noise_level,
            "audio_quality": self.audio_quality,
            "overall_score": self.overall_score,
        }


@dataclass(frozen=True)
class QualityWeights:
    sharpness: float = 0.3
    exposure: float = 0.2
    motion_blur: float = 0.2
    noise_level: float = 0.15
    audio_quality: float = 0.15

    def normalised(self) -> tuple[float, float, float, float, float]:
        components = [
            max(self.sharpness, 0.0),
            max(self.exposure, 0.0),
            max(self.motion_blur, 0.0),
            max(self.noise_level, 0.0),
            max(self.audio_quality, 0.0),
        ]
        total = sum(components)
        if total <= 0:
            return (1.0, 0.0, 0.0, 0.0, 0.0)
        return tuple(component / total for component in components)


class QualityAnalysisError(Exception):
    pass


class QualityService:
    def __init__(
        self,
        settings: Settings,
        ffmpeg_service: FFmpegService,
        *,
        weights: QualityWeights | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._settings = settings
        self._ffmpeg = ffmpeg_service
        self._weights = weights or QualityWeights()
        self._logger = logger or logging.getLogger("backend.app.services.video.quality")

    def analyse_video_quality(
        self,
        video_path: Path,
        *,
        sample_count: int = 10,
    ) -> QualityMetrics:
        if not video_path.exists():
            raise QualityAnalysisError(f"Video file not found: {video_path}")

        try:
            metadata = self._ffmpeg.get_video_metadata(video_path)
            if metadata.duration is None or metadata.duration <= 0:
                raise QualityAnalysisError("Video duration could not be determined")

            sharpness = self._analyse_sharpness(video_path, metadata.duration, sample_count)
            exposure = self._analyse_exposure(video_path, metadata.duration, sample_count)
            motion_blur = self._analyse_motion_blur(video_path, metadata.duration, sample_count)
            noise_level = self._analyse_noise(video_path, metadata.duration, sample_count)

            audio_quality: float | None = None
            try:
                audio_quality = self._analyse_audio_quality(video_path)
            except Exception as exc:
                self._logger.warning(
                    "Audio quality analysis failed, proceeding without audio metrics",
                    exc_info=exc,
                    extra={"extra": {"video_path": str(video_path)}},
                )

            overall_score = self._compute_overall_score(
                sharpness, exposure, motion_blur, noise_level, audio_quality
            )

            return QualityMetrics(
                sharpness=sharpness,
                exposure=exposure,
                motion_blur=motion_blur,
                noise_level=noise_level,
                audio_quality=audio_quality,
                overall_score=overall_score,
            )

        except cv2.error as exc:
            raise QualityAnalysisError(f"OpenCV error during quality analysis: {exc}") from exc
        except Exception as exc:
            self._logger.exception("Unexpected error during quality analysis", exc_info=exc)
            raise QualityAnalysisError(f"Quality analysis failed: {exc}") from exc

    def _analyse_sharpness(self, video_path: Path, duration: float, sample_count: int) -> float:
        cap = cv2.VideoCapture(str(video_path))
        try:
            timestamps = self._generate_sample_timestamps(duration, sample_count)
            sharpness_scores: List[float] = []

            for timestamp in timestamps:
                frame = self._extract_frame_at_timestamp(cap, timestamp, duration)
                if frame is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                    normalized = min(1.0, laplacian_var / 1000.0)
                    sharpness_scores.append(normalized)

            return float(np.mean(sharpness_scores)) if sharpness_scores else 0.0
        finally:
            cap.release()

    def _analyse_exposure(self, video_path: Path, duration: float, sample_count: int) -> float:
        cap = cv2.VideoCapture(str(video_path))
        try:
            timestamps = self._generate_sample_timestamps(duration, sample_count)
            exposure_scores: List[float] = []

            for timestamp in timestamps:
                frame = self._extract_frame_at_timestamp(cap, timestamp, duration)
                if frame is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    mean_brightness = gray.mean()
                    ideal_brightness = 128.0
                    deviation = abs(mean_brightness - ideal_brightness) / ideal_brightness
                    score = max(0.0, 1.0 - deviation)
                    exposure_scores.append(score)

            return float(np.mean(exposure_scores)) if exposure_scores else 0.0
        finally:
            cap.release()

    def _analyse_motion_blur(self, video_path: Path, duration: float, sample_count: int) -> float:
        cap = cv2.VideoCapture(str(video_path))
        try:
            timestamps = self._generate_sample_timestamps(duration, sample_count)
            motion_blur_scores: List[float] = []

            for timestamp in timestamps:
                frame = self._extract_frame_at_timestamp(cap, timestamp, duration)
                if frame is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
                    variance = laplacian.var()
                    blur_score = 1.0 - min(1.0, variance / 500.0)
                    motion_blur_scores.append(blur_score)

            return float(np.mean(motion_blur_scores)) if motion_blur_scores else 0.0
        finally:
            cap.release()

    def _analyse_noise(self, video_path: Path, duration: float, sample_count: int) -> float:
        cap = cv2.VideoCapture(str(video_path))
        try:
            timestamps = self._generate_sample_timestamps(duration, sample_count)
            noise_scores: List[float] = []

            for timestamp in timestamps:
                frame = self._extract_frame_at_timestamp(cap, timestamp, duration)
                if frame is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    noise_estimate = self._estimate_noise_level(gray)
                    normalized = 1.0 - min(1.0, noise_estimate / 50.0)
                    noise_scores.append(normalized)

            return float(np.mean(noise_scores)) if noise_scores else 0.0
        finally:
            cap.release()

    def _analyse_audio_quality(self, video_path: Path) -> float:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            temp_audio_path = Path(temp_audio.name)

        try:
            audio_path = self._ffmpeg.extract_audio_track(video_path, output_format="wav")
            y, sr = librosa.load(str(audio_path), sr=None)

            rms = librosa.feature.rms(y=y)[0]
            mean_rms = float(np.mean(rms))
            normalized_level = min(1.0, mean_rms * 10.0)

            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            mean_centroid = float(np.mean(spectral_centroid))
            clarity_score = min(1.0, mean_centroid / 3000.0)

            audio_score = (normalized_level * 0.6 + clarity_score * 0.4)

            audio_path.unlink(missing_ok=True)

            return audio_score
        except Exception:
            temp_audio_path.unlink(missing_ok=True)
            raise

    def _estimate_noise_level(self, gray_frame: np.ndarray) -> float:
        h, w = gray_frame.shape
        crop_h = h // 4
        crop_w = w // 4
        center_h = h // 2
        center_w = w // 2

        center_region = gray_frame[
            center_h - crop_h : center_h + crop_h,
            center_w - crop_w : center_w + crop_w,
        ]

        sigma = np.std(center_region)
        return float(sigma)

    def _extract_frame_at_timestamp(
        self,
        cap: cv2.VideoCapture,
        timestamp: float,
        duration: float,
    ) -> np.ndarray | None:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30.0

        frame_number = int(timestamp * fps)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)

        ret, frame = cap.read()
        if not ret or frame is None:
            return None

        return frame

    def _generate_sample_timestamps(self, duration: float, sample_count: int) -> List[float]:
        if sample_count <= 0:
            return []
        if sample_count == 1:
            return [duration / 2.0]

        timestamps: List[float] = []
        step = duration / (sample_count + 1)
        for i in range(1, sample_count + 1):
            timestamps.append(step * i)

        return timestamps

    def _compute_overall_score(
        self,
        sharpness: float,
        exposure: float,
        motion_blur: float,
        noise_level: float,
        audio_quality: float | None,
    ) -> float:
        weights = self._weights.normalised()
        score = (
            sharpness * weights[0]
            + exposure * weights[1]
            + (1.0 - motion_blur) * weights[2]
            + noise_level * weights[3]
        )

        if audio_quality is not None:
            score += audio_quality * weights[4]
        else:
            score = score / (1.0 - weights[4])

        return min(1.0, max(0.0, score))


__all__ = ["QualityService", "QualityMetrics", "QualityWeights", "QualityAnalysisError"]
