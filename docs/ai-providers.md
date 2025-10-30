# AI Provider Configuration & Fallback Strategy

The AI layer is designed to orchestrate multiple model providers with graceful degradation, deterministic auditing, and offline-friendly defaults. This document explains how to configure keys, tune the fallback order, and account for privacy considerations when connecting to third-party services.

## Provider Registry

The backend ships with adapters for the following providers (see `backend/app/services/ai/providers/`):

| Provider | Capabilities | Required SDK | Environment Variable |
| --- | --- | --- | --- |
| OpenAI | Chat, embeddings, Whisper transcription | `openai` | `OPENAI_API_KEY` |
| Google Gemini | Chat, embeddings | `google-generativeai` | `GEMINI_API_KEY` |
| Anthropic Claude | Chat | `anthropic` | `ANTHROPIC_API_KEY` |
| Groq | Chat | `groq` | `GROQ_API_KEY` |

Each adapter lazily imports its SDK and checks for the presence of the associated API key. Missing keys (or SDK modules) automatically disable the provider without raising errors at startup.

## Environment Variables

Key configuration is inherited from `.env` (see `.env.example`). The most relevant settings are:

| Variable | Default | Description |
| --- | --- | --- |
| `AI_PROVIDER_ORDER` | `openai,gemini,claude,groq` | Ordered, comma-separated list of provider names (`openai`, `gemini`, `claude`, `groq`). The router respects this order when choosing a provider. |
| `AI_PROVIDER_TIMEOUT_SECONDS` | `30` | Upper bound for each provider attempt. Set to `0` to disable request timeouts (not recommended). |
| `AI_PROVIDER_RETRIES` | `1` | Number of retries *per provider* before moving to the next fallback. |
| `AI_PROVIDER_RETRY_BASE_DELAY` | `0.5` | Initial backoff delay in seconds. |
| `AI_PROVIDER_RETRY_BACKOFF_FACTOR` | `2.0` | Multiplier applied per retry attempt (exponential backoff). |
| `OPENAI_API_KEY` | – | Enables the OpenAI adapter when provided. |
| `GEMINI_API_KEY` | – | Enables the Gemini adapter. |
| `ANTHROPIC_API_KEY` | – | Enables the Claude adapter. |
| `GROQ_API_KEY` | – | Enables the Groq adapter. |

## Fallback Behaviour

`AIProviderRouter` coordinates all provider calls:

1. Build the ordered provider list from `AI_PROVIDER_ORDER` (de-duplicated, case-insensitive).
2. Skip providers that fail configuration (`ProviderNotConfiguredError`).
3. Attempt the call with retries and exponential backoff as configured.
4. Capture structured `ProviderErrorInfo` for each failure (status code, retryable flag, provider name).
5. Continue to the next provider until a response succeeds or every provider fails.
6. Raise `AllProvidersFailedError` with the accumulated diagnostics if no provider can fulfil the request.

The router logs success and failure metrics (`latency_ms`, token usage, finish reasons) to aid observability dashboards.

### Overriding Order Per Request

`AIProviderRouter.generate_text` accepts a `provider_order` override. API services can provide a custom priority list for special workloads (e.g., preferring Groq for cost-sensitive batches). Validate names against the registry to avoid silent skips.

### Extending the Registry

1. Implement a subclass of `BaseAIProvider` in `backend/app/services/ai/providers/`.
2. Set `name` to the identifier used in `AI_PROVIDER_ORDER`.
3. Register the class inside `__init__.py` via the `PROVIDER_REGISTRY` mapping.
4. Add any new environment variables to `.env.example` and document them here.

## Privacy & Data Minimisation

- **Payload hygiene:** Only the `prompt`/`messages` payload is sent to providers. Media assets remain on local storage unless your custom provider streams audio bytes (e.g., transcription). When transcription is enabled, temporary files are read from disk and deleted by pipeline services once processed.
- **Logging:** Sensitive content is not persisted in logs. Success logs capture metadata (token counts, model name) but no raw completion text. Failures record error codes and safe messages.
- **Data residency:** Use providers that match your compliance requirements, or inject an on-prem adapter that talks to a self-hosted model. You can ship a custom provider that wraps local inference engines (e.g., Ollama, vLLM) without touching cloud services.

## Operating Offline or in Air-Gapped Environments

- Leave `AI_PROVIDER_ORDER` blank (or point it to a custom offline provider) to disable outbound calls entirely.
- Provide local model endpoints via new provider adapters. Because providers receive normalised messages, wrappers for Hugging Face Text Generation Inference or GGML runners are straightforward.
- Disable retries and lower timeouts to avoid blocking job execution when no providers are reachable.
- Combine with the offline deployment notes in [`docs/README.md`](./README.md#offline--air-gapped-deployment-notes) to keep queue workers running without internet access.

## Troubleshooting

| Symptom | Likely Cause | Resolution |
| --- | --- | --- |
| All requests fail immediately with `Provider is not configured.` | Missing API key or SDK import | Install the vendor SDK (`pip install openai`) and provide the key in `.env`. |
| Fallback never advances beyond the first provider | Provider is marked retryable and `AI_PROVIDER_RETRIES` is high | Reduce retries or mark errors as non-retryable in your provider implementation. |
| Latency spikes when multiple providers are configured | Sequential fallback attempts | Tighten timeouts and ensure the preferred provider is first in `AI_PROVIDER_ORDER`. |
| Sensitive text appears in logs | Custom logging configuration overriding defaults | Ensure `extra` payloads are redacted in downstream handlers or trim log level to `WARNING` in production. |

## Related Resources

- [`backend/app/services/ai/router.py`](../backend/app/services/ai/router.py) – Router implementation with fallback logic.
- [`backend/tests/test_ai_router.py`](../backend/tests/test_ai_router.py) – Unit tests covering error propagation and ordered fallbacks.
- [`docs/api.md`](./api.md) – REST endpoints that expose AI-powered operations.
