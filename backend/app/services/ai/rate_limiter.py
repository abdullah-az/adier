from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Deque

from .exceptions import AIProviderRateLimitError


class SlidingWindowRateLimiter:
    """Very small sliding window limiter suitable for async flows."""

    def __init__(self, name: str, max_calls_per_minute: float | None) -> None:
        self.name = name
        self.max_calls_per_minute = max_calls_per_minute
        self._timestamps: Deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        if not self.max_calls_per_minute or self.max_calls_per_minute <= 0:
            return

        async with self._lock:
            now = time.monotonic()
            window_seconds = 60.0
            boundary = now - window_seconds
            while self._timestamps and self._timestamps[0] < boundary:
                self._timestamps.popleft()

            if len(self._timestamps) >= int(self.max_calls_per_minute):
                raise AIProviderRateLimitError(
                    f"Provider '{self.name}' is rate limited to {self.max_calls_per_minute} calls/minute"
                )

            self._timestamps.append(now)
