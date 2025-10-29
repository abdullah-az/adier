from __future__ import annotations

import re
import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_ERROR_LINE_RE = re.compile(r"(?P<level>error|fatal|warning)[:\s]+(?P<message>.+)", re.IGNORECASE)


@contextmanager
def temporary_workspace(base_dir: Path, *, prefix: str = "ffmpeg-") -> Iterator[Path]:
    """Create a temporary working directory under the configured base path."""

    base_dir.mkdir(parents=True, exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix=prefix, dir=base_dir))
    try:
        yield workspace
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def parse_ffmpeg_error(stderr: str) -> str:
    """Extract a human friendly error message from FFmpeg stderr output."""

    if not stderr:
        return "Unknown FFmpeg error"

    lines = [line.strip() for line in stderr.strip().splitlines() if line.strip()]
    for line in reversed(lines):
        match = _ERROR_LINE_RE.search(line)
        if match:
            return match.group("message").strip()

    return lines[-1] if lines else "Unknown FFmpeg error"
