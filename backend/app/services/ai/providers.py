"""Concrete AI provider implementations and registry helpers."""

from __future__ import annotations

import asyncio
import base64
import json
from pathlib import Path
from typing import Any, Iterable, Optional

from loguru import logger

from app.services.ai.base import (
    AIProvider,
    ProviderCapabilityNotSupportedError,
    ProviderInvocationError,
    ProviderNotConfiguredError,
    ProviderQuotaError,
    ProviderRateLimitError,
    ProviderResult,
    ProviderTask,
)

# Third-party SDKs are optional dependencies. Providers become available when the
# corresponding package is installed and an API key is supplied.
try:  # pragma: no cover - optional import
    from openai import OpenAI
    from openai import APIStatusError, RateLimitError as OpenAIRateLimitError
except ImportError:  # pragma: no cover - handled by provider availability checks
    OpenAI = None  # type: ignore[assignment]
    APIStatusError = OpenAIRateLimitError = None  # type: ignore[assignment]

try:  # pragma: no cover - optional import
    import google.generativeai as genai
except ImportError:  # pragma: no cover - handled gracefully
    genai = None  # type: ignore[assignment]

try:  # pragma: no cover - optional import
    import anthropic
except ImportError:  # pragma: no cover - handled gracefully
    anthropic = None  # type: ignore[assignment]

try:  # pragma: no cover - optional import
    from groq import Groq
    from groq import RateLimitError as GroqRateLimitError
except ImportError:  # pragma: no cover - handled gracefully
    Groq = None  # type: ignore[assignment]
    GroqRateLimitError = None  # type: ignore[assignment]


def _safe_usage_lookup(response: Any) -> dict[str, Any]:
    if response is None:
        return {}
    if isinstance(response, dict):
        return response.get("usage") or {}
    if hasattr(response, "model_dump"):
        payload = response.model_dump()
        if isinstance(payload, dict):
            return payload.get("usage") or {}
    if hasattr(response, "to_dict"):
        payload = response.to_dict()
        if isinstance(payload, dict):
            return payload.get("usage") or {}
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}
    if isinstance(usage, dict):
        return usage
    if hasattr(usage, "model_dump"):
        return usage.model_dump()
    return {}


def _ensure_bytes(data: Any) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        path = Path(data)
        if path.exists():
            return path.read_bytes()
        try:
            return base64.b64decode(data, validate=True)
        except Exception:  # pragma: no cover - defensive fallback
            return data.encode("utf-8", errors="ignore")
    if isinstance(data, Path):
        return data.read_bytes()
    raise ValueError("Unsupported audio/document payload for provider request")


class OpenAIProvider(AIProvider):
    provider_id = "openai"
    display_name = "OpenAI"
    capabilities = frozenset(
        {
            ProviderTask.SCENE_ANALYSIS,
            ProviderTask.TRANSCRIPTION,
            ProviderTask.HIGHLIGHT_GENERATION,
            ProviderTask.TEXT_EXTRACTION,
        }
    )

    def __init__(
        self,
        *,
        api_key: Optional[str],
        vision_model: str,
        text_model: str,
        transcription_model: str,
        cost_currency: str = "USD",
        rate_limits: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(rate_limits=rate_limits)
        self.api_key = api_key
        self.vision_model = vision_model
        self.text_model = text_model
        self.transcription_model = transcription_model
        self.cost_currency = cost_currency
        self._client: Optional[OpenAI] = None
        if api_key and OpenAI is not None:
            self._client = OpenAI(api_key=api_key)
            self._configured = True
        else:
            logger.debug("OpenAI provider not configured", have_sdk=OpenAI is not None, has_key=bool(api_key))

    async def analyze_scene(
        self,
        *,
        video_frames: list[Any],
        transcript: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        self._ensure_capability(ProviderTask.SCENE_ANALYSIS)
        self._ensure_configured()
        assert self._client is not None  # for mypy

        frame_descriptions = kwargs.get("frame_descriptions") or [
            f"Frame {index + 1}: {str(frame)[:80]}" for index, frame in enumerate(video_frames[:6])
        ]
        prompt = (
            "You are an expert video editor. Analyse the provided frames and optional transcript. "
            "Return a JSON list named scenes where each item has timestamp, confidence, and summary fields."
        )
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "input_text", "text": json.dumps({"frames": frame_descriptions})},
                ],
            }
        ]
        if transcript:
            messages[0]["content"].append({"type": "input_text", "text": transcript[:4000]})

        def _call() -> Any:
            return self._client.responses.create(
                model=self.vision_model,
                input=messages,
                response_format={"type": "json_object"},
                max_output_tokens=1024,
            )

        try:
            response = await asyncio.to_thread(_call)
        except OpenAIRateLimitError as exc:  # pragma: no cover - network path
            retry_after = getattr(exc, "retry_after", None)
            raise ProviderRateLimitError(str(exc), retry_after=retry_after) from exc
        except APIStatusError as exc:  # pragma: no cover - network path
            if getattr(exc, "status_code", None) == 429:
                retry_after = getattr(exc, "response", {}).get("retry_after") if hasattr(exc, "response") else None
                raise ProviderRateLimitError(str(exc), retry_after=retry_after) from exc
            raise ProviderInvocationError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive network path
            raise ProviderInvocationError(str(exc)) from exc

        usage = _safe_usage_lookup(response)
        output_text = getattr(response, "output_text", None)
        if not output_text:
            if hasattr(response, "output") and response.output:
                output_text = "\n".join(chunk.text for chunk in response.output if getattr(chunk, "text", None))

        try:
            payload = json.loads(output_text) if output_text else {}
        except json.JSONDecodeError:
            payload = {"scenes": []}

        scenes = payload.get("scenes") or []
        metadata = {"usage": usage, "raw": output_text}
        return ProviderResult(data={"scenes": scenes}, cost=usage.get("total_cost", 0.0), metadata=metadata, raw=response)

    async def transcribe_audio(
        self,
        *,
        audio_source: Any,
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        self._ensure_capability(ProviderTask.TRANSCRIPTION)
        self._ensure_configured()
        assert self._client is not None

        audio_bytes = _ensure_bytes(audio_source)

        def _call() -> Any:
            return self._client.audio.transcriptions.create(
                model=self.transcription_model,
                file=audio_bytes,
                response_format="verbose_json",
            )

        try:
            response = await asyncio.to_thread(_call)
        except OpenAIRateLimitError as exc:  # pragma: no cover - network path
            raise ProviderRateLimitError(str(exc)) from exc
        except APIStatusError as exc:  # pragma: no cover - network path
            raise ProviderInvocationError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive network path
            raise ProviderInvocationError(str(exc)) from exc

        transcript = getattr(response, "text", None) or response.get("text") if isinstance(response, dict) else None
        usage = _safe_usage_lookup(response)
        metadata = {"usage": usage, "segments": getattr(response, "segments", None)}
        return ProviderResult(
            data={"transcript": transcript or "", "language": language or kwargs.get("language", "en")},
            cost=usage.get("total_cost", 0.0),
            metadata=metadata,
            raw=response,
        )

    async def generate_highlights(
        self,
        *,
        transcript: str,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        self._ensure_capability(ProviderTask.HIGHLIGHT_GENERATION)
        self._ensure_configured()
        assert self._client is not None

        prompt = (
            "Summarise the transcript into 3 engaging bullet highlights for a video description. "
            "Respond as a JSON object with a 'highlights' array."
        )

        def _call() -> Any:
            return self._client.responses.create(
                model=self.text_model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "input_text", "text": transcript[:6000]},
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                max_output_tokens=512,
            )

        try:
            response = await asyncio.to_thread(_call)
        except OpenAIRateLimitError as exc:  # pragma: no cover - network path
            raise ProviderRateLimitError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive network path
            raise ProviderInvocationError(str(exc)) from exc

        usage = _safe_usage_lookup(response)
        output_text = getattr(response, "output_text", None)
        try:
            payload = json.loads(output_text) if output_text else {}
        except json.JSONDecodeError:
            payload = {"highlights": []}
        result_metadata = {"usage": usage}
        if metadata:
            result_metadata.update(metadata)
        return ProviderResult(
            data={"highlights": payload.get("highlights", [])},
            cost=usage.get("total_cost", 0.0),
            metadata=result_metadata,
            raw=response,
        )

    async def extract_text(self, *, document: Any, **kwargs: Any) -> ProviderResult:
        self._ensure_capability(ProviderTask.TEXT_EXTRACTION)
        self._ensure_configured()
        assert self._client is not None

        document_bytes = _ensure_bytes(document)
        prompt = "Extract all readable text content from the provided document. Respond with JSON {\"text\": string}."

        def _call() -> Any:
            return self._client.responses.create(
                model=self.text_model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "input_text", "text": document_bytes.decode('utf-8', errors='ignore')[:6000]},
                        ],
                    }
                ],
                response_format={"type": "json_object"},
            )

        try:
            response = await asyncio.to_thread(_call)
        except OpenAIRateLimitError as exc:  # pragma: no cover - network path
            raise ProviderRateLimitError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive network path
            raise ProviderInvocationError(str(exc)) from exc

        usage = _safe_usage_lookup(response)
        output_text = getattr(response, "output_text", None)
        try:
            payload = json.loads(output_text) if output_text else {}
        except json.JSONDecodeError:
            payload = {"text": ""}
        return ProviderResult(data={"text": payload.get("text", "")}, cost=usage.get("total_cost", 0.0), metadata={"usage": usage}, raw=response)


class GeminiProvider(AIProvider):
    provider_id = "gemini"
    display_name = "Google Gemini"
    capabilities = frozenset(
        {
            ProviderTask.SCENE_ANALYSIS,
            ProviderTask.TRANSCRIPTION,
            ProviderTask.HIGHLIGHT_GENERATION,
            ProviderTask.TEXT_EXTRACTION,
        }
    )

    def __init__(
        self,
        *,
        api_key: Optional[str],
        vision_model: str,
        text_model: str,
        cost_currency: str = "USD",
        rate_limits: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(rate_limits=rate_limits)
        self.api_key = api_key
        self.vision_model = vision_model
        self.text_model = text_model
        self.cost_currency = cost_currency
        self._vision_model = None
        self._text_model = None
        if api_key and genai is not None:
            genai.configure(api_key=api_key)
            self._vision_model = genai.GenerativeModel(self.vision_model)
            self._text_model = genai.GenerativeModel(self.text_model)
            self._configured = True
        else:
            logger.debug(
                "Gemini provider not configured",
                have_sdk=genai is not None,
                has_key=bool(api_key),
            )

    async def analyze_scene(
        self,
        *,
        video_frames: list[Any],
        transcript: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        self._ensure_capability(ProviderTask.SCENE_ANALYSIS)
        self._ensure_configured()
        assert self._vision_model is not None

        def _prepare_inputs() -> list[Any]:
            inputs: list[Any] = [
                {"role": "user", "parts": ["Analyse the frames and return JSON scenes with timestamp and summary"]},
            ]
            frame_parts: list[Any] = []
            for frame in video_frames[:8]:
                if isinstance(frame, dict) and {"mime_type", "data"} <= frame.keys():
                    frame_parts.append(frame)
                else:
                    try:
                        frame_bytes = _ensure_bytes(frame)
                    except ValueError:
                        frame_parts.append(str(frame))
                    else:
                        frame_parts.append(genai.types.Blob(mime_type="image/png", data=frame_bytes))
            if frame_parts:
                inputs.append({"role": "user", "parts": frame_parts})
            if transcript:
                inputs.append({"role": "user", "parts": [transcript[:6000]]})
            return inputs

        inputs = await asyncio.to_thread(_prepare_inputs)

        def _call() -> Any:
            return self._vision_model.generate_content(inputs)

        try:
            response = await asyncio.to_thread(_call)
        except Exception as exc:  # pragma: no cover - network path
            message = str(exc)
            if "429" in message:
                raise ProviderRateLimitError(message) from exc
            raise ProviderInvocationError(message) from exc

        text = response.text if hasattr(response, "text") else getattr(response, "candidates", [])
        try:
            payload = json.loads(text) if isinstance(text, str) else {}
        except json.JSONDecodeError:
            payload = {"scenes": []}
        metadata = {"raw": text}
        return ProviderResult(data={"scenes": payload.get("scenes", [])}, metadata=metadata, raw=response)

    async def transcribe_audio(
        self,
        *,
        audio_source: Any,
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        self._ensure_capability(ProviderTask.TRANSCRIPTION)
        self._ensure_configured()
        assert self._text_model is not None

        audio_bytes = _ensure_bytes(audio_source)

        def _call() -> Any:
            return self._text_model.generate_content([
                "Transcribe the provided audio base64 string into text. Respond JSON {\"transcript\": str}.",
                base64.b64encode(audio_bytes).decode("utf-8"),
            ])

        try:
            response = await asyncio.to_thread(_call)
        except Exception as exc:  # pragma: no cover - network path
            message = str(exc)
            if "429" in message:
                raise ProviderRateLimitError(message) from exc
            raise ProviderInvocationError(message) from exc

        text = getattr(response, "text", None)
        try:
            payload = json.loads(text) if text else {}
        except json.JSONDecodeError:
            payload = {"transcript": ""}
        metadata = {"raw": text}
        return ProviderResult(
            data={"transcript": payload.get("transcript", ""), "language": language or "auto"},
            metadata=metadata,
            raw=response,
        )

    async def generate_highlights(
        self,
        *,
        transcript: str,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        self._ensure_capability(ProviderTask.HIGHLIGHT_GENERATION)
        self._ensure_configured()
        assert self._text_model is not None

        def _call() -> Any:
            return self._text_model.generate_content([
                "Create three compelling highlights from the transcript as JSON {\"highlights\": [str]}.",
                transcript[:6000],
            ])

        try:
            response = await asyncio.to_thread(_call)
        except Exception as exc:  # pragma: no cover - network path
            message = str(exc)
            if "429" in message:
                raise ProviderRateLimitError(message) from exc
            raise ProviderInvocationError(message) from exc

        text = getattr(response, "text", None)
        try:
            payload = json.loads(text) if text else {}
        except json.JSONDecodeError:
            payload = {"highlights": []}
        meta = {"raw": text}
        if metadata:
            meta.update(metadata)
        return ProviderResult(data={"highlights": payload.get("highlights", [])}, metadata=meta, raw=response)

    async def extract_text(self, *, document: Any, **kwargs: Any) -> ProviderResult:
        self._ensure_capability(ProviderTask.TEXT_EXTRACTION)
        self._ensure_configured()
        assert self._text_model is not None

        document_bytes = _ensure_bytes(document)

        def _call() -> Any:
            return self._text_model.generate_content([
                "Extract text from this document content and respond JSON {\"text\": str}.",
                document_bytes.decode("utf-8", errors="ignore")[:6000],
            ])

        try:
            response = await asyncio.to_thread(_call)
        except Exception as exc:  # pragma: no cover - network path
            message = str(exc)
            if "429" in message:
                raise ProviderRateLimitError(message) from exc
            raise ProviderInvocationError(message) from exc

        text = getattr(response, "text", None)
        try:
            payload = json.loads(text) if text else {}
        except json.JSONDecodeError:
            payload = {"text": ""}
        return ProviderResult(data={"text": payload.get("text", "")}, metadata={"raw": text}, raw=response)


class ClaudeProvider(AIProvider):
    provider_id = "claude"
    display_name = "Anthropic Claude"
    capabilities = frozenset(
        {
            ProviderTask.SCENE_ANALYSIS,
            ProviderTask.HIGHLIGHT_GENERATION,
            ProviderTask.TEXT_EXTRACTION,
        }
    )

    def __init__(
        self,
        *,
        api_key: Optional[str],
        model: str,
        cost_currency: str = "USD",
        rate_limits: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(rate_limits=rate_limits)
        self.api_key = api_key
        self.model = model
        self.cost_currency = cost_currency
        self._client = None
        if api_key and anthropic is not None:
            self._client = anthropic.Anthropic(api_key=api_key)
            self._configured = True
        else:
            logger.debug(
                "Claude provider not configured",
                have_sdk=anthropic is not None,
                has_key=bool(api_key),
            )

    async def analyze_scene(
        self,
        *,
        video_frames: list[Any],
        transcript: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        if not self.supports(ProviderTask.SCENE_ANALYSIS):
            raise ProviderCapabilityNotSupportedError("Claude vision support not enabled")
        self._ensure_configured()
        assert self._client is not None

        prompt = (
            "Analyse the following frames and optional transcript. Respond JSON with scenes list containing "
            "timestamp, summary, confidence."
        )
        content_blocks = [
            {"type": "text", "text": prompt},
            {"type": "text", "text": json.dumps(video_frames[:6])},
        ]
        if transcript:
            content_blocks.append({"type": "text", "text": transcript[:6000]})

        def _call() -> Any:
            return self._client.messages.create(
                model=self.model,
                max_output_tokens=1024,
                messages=[{"role": "user", "content": content_blocks}],
            )

        try:
            response = await asyncio.to_thread(_call)
        except anthropic.RateLimitError as exc:  # pragma: no cover - network path
            raise ProviderRateLimitError(str(exc)) from exc
        except anthropic.APIError as exc:  # pragma: no cover - network path
            if exc.status_code == 403:
                raise ProviderQuotaError(str(exc)) from exc
            raise ProviderInvocationError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive network path
            raise ProviderInvocationError(str(exc)) from exc

        text = "".join(block.text for block in response.content if getattr(block, "text", None))
        try:
            payload = json.loads(text) if text else {}
        except json.JSONDecodeError:
            payload = {"scenes": []}
        metadata = {"raw": text}
        return ProviderResult(data={"scenes": payload.get("scenes", [])}, metadata=metadata, raw=response)

    async def generate_highlights(
        self,
        *,
        transcript: str,
        metadata: Optional[dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        self._ensure_capability(ProviderTask.HIGHLIGHT_GENERATION)
        self._ensure_configured()
        assert self._client is not None

        prompt = "Create three compelling highlights from transcript as JSON {\"highlights\":[str]}"

        def _call() -> Any:
            return self._client.messages.create(
                model=self.model,
                max_output_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "text", "text": transcript[:6000]},
                        ],
                    }
                ],
            )

        try:
            response = await asyncio.to_thread(_call)
        except anthropic.RateLimitError as exc:  # pragma: no cover - network path
            raise ProviderRateLimitError(str(exc)) from exc
        except anthropic.APIError as exc:  # pragma: no cover - network path
            raise ProviderInvocationError(str(exc)) from exc

        text = "".join(block.text for block in response.content if getattr(block, "text", None))
        try:
            payload = json.loads(text) if text else {}
        except json.JSONDecodeError:
            payload = {"highlights": []}
        meta = {"raw": text}
        if metadata:
            meta.update(metadata)
        return ProviderResult(data={"highlights": payload.get("highlights", [])}, metadata=meta, raw=response)

    async def extract_text(self, *, document: Any, **kwargs: Any) -> ProviderResult:
        self._ensure_capability(ProviderTask.TEXT_EXTRACTION)
        self._ensure_configured()
        assert self._client is not None

        prompt = "Extract text from document into JSON {\"text\": str}"
        content = _ensure_bytes(document).decode("utf-8", errors="ignore")[:6000]

        def _call() -> Any:
            return self._client.messages.create(
                model=self.model,
                max_output_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "text", "text": content},
                        ],
                    }
                ],
            )

        try:
            response = await asyncio.to_thread(_call)
        except anthropic.RateLimitError as exc:  # pragma: no cover - network path
            raise ProviderRateLimitError(str(exc)) from exc
        except anthropic.APIError as exc:  # pragma: no cover - network path
            raise ProviderInvocationError(str(exc)) from exc

        text = "".join(block.text for block in response.content if getattr(block, "text", None))
        try:
            payload = json.loads(text) if text else {}
        except json.JSONDecodeError:
            payload = {"text": ""}
        return ProviderResult(data={"text": payload.get("text", "")}, metadata={"raw": text}, raw=response)


class GroqProvider(AIProvider):
    provider_id = "groq"
    display_name = "Groq"
    capabilities = frozenset({ProviderTask.TRANSCRIPTION})

    def __init__(
        self,
        *,
        api_key: Optional[str],
        whisper_model: str,
        cost_currency: str = "USD",
        rate_limits: Optional[dict[str, Any]] = None,
    ) -> None:
        super().__init__(rate_limits=rate_limits)
        self.api_key = api_key
        self.whisper_model = whisper_model
        self.cost_currency = cost_currency
        self._client = None
        if api_key and Groq is not None:
            self._client = Groq(api_key=api_key)
            self._configured = True
        else:
            logger.debug(
                "Groq provider not configured",
                have_sdk=Groq is not None,
                has_key=bool(api_key),
            )

    async def analyze_scene(self, *, video_frames: list[Any], transcript: Optional[str] = None, **kwargs: Any) -> ProviderResult:
        raise ProviderCapabilityNotSupportedError("Groq provider only supports transcription")

    async def transcribe_audio(
        self,
        *,
        audio_source: Any,
        language: Optional[str] = None,
        **kwargs: Any,
    ) -> ProviderResult:
        self._ensure_capability(ProviderTask.TRANSCRIPTION)
        self._ensure_configured()
        assert self._client is not None

        audio_bytes = _ensure_bytes(audio_source)

        def _call() -> Any:
            return self._client.audio.transcriptions.create(
                model=self.whisper_model,
                file=audio_bytes,
                response_format="verbose_json",
            )

        try:
            response = await asyncio.to_thread(_call)
        except GroqRateLimitError as exc:  # pragma: no cover - network path
            raise ProviderRateLimitError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive network path
            raise ProviderInvocationError(str(exc)) from exc

        transcript = getattr(response, "text", None) or response.get("text") if isinstance(response, dict) else None
        metadata = {"segments": getattr(response, "segments", None)}
        return ProviderResult(data={"transcript": transcript or "", "language": language or "auto"}, metadata=metadata, raw=response)

    async def generate_highlights(self, *, transcript: str, metadata: Optional[dict[str, Any]] = None, **kwargs: Any) -> ProviderResult:
        raise ProviderCapabilityNotSupportedError("Groq provider only supports transcription")

    async def extract_text(self, *, document: Any, **kwargs: Any) -> ProviderResult:
        raise ProviderCapabilityNotSupportedError("Groq provider only supports transcription")
