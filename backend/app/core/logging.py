from __future__ import annotations

import json
import logging
import logging.config
from datetime import datetime
from typing import Any, Dict

from .config import Settings


class JsonLogFormatter(logging.Formatter):
    """Formatter that outputs log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        log_record = self._build_record(record)
        return json.dumps(log_record, default=str)

    def _build_record(self, record: logging.LogRecord) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            data["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            data["stacktrace"] = record.stack_info

        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            data.update(extra)
        return data


class ConsoleLogFormatter(logging.Formatter):
    default_msec_format = "%s.%03d"

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        record.asctime = self.formatTime(record, self.datefmt)
        message = super().format(record)
        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"
        return message


def configure_logging(settings: Settings) -> None:
    """Configure application-wide logging according to settings."""

    if settings.log_format == "json":
        formatter = JsonLogFormatter()
    else:
        formatter = ConsoleLogFormatter(fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    
    handler = logging.StreamHandler()
    handler.setLevel(settings.log_level.upper())
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level.upper())
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.handlers.clear()
    uvicorn_logger.addHandler(handler)
    uvicorn_logger.setLevel(settings.log_level.upper())
    
    uvicorn_error = logging.getLogger("uvicorn.error")
    uvicorn_error.handlers.clear()
    uvicorn_error.addHandler(handler)
    uvicorn_error.setLevel(settings.log_level.upper())
    
    access_handler = logging.StreamHandler()
    access_handler.setFormatter(logging.Formatter("%(message)s"))
    uvicorn_access = logging.getLogger("uvicorn.access")
    uvicorn_access.handlers.clear()
    uvicorn_access.addHandler(access_handler)
    uvicorn_access.setLevel("INFO")


def get_logging_config(settings: Settings, formatter_name: str) -> Dict[str, Any]:
    import sys
    module = sys.modules[__name__]
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": lambda: module.JsonLogFormatter(),
            },
            "console": {
                "()": lambda: module.ConsoleLogFormatter(
                    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
                ),
            },
            "access": {
                "()": "logging.Formatter",
                "format": "%(message)s",
            },
        },
        "handlers": {
            "default": {
                "level": settings.log_level.upper(),
                "class": "logging.StreamHandler",
                "formatter": formatter_name,
            },
            "uvicorn.access": {
                "class": "logging.StreamHandler",
                "formatter": "access",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["default"], "level": settings.log_level.upper(), "propagate": False},
            "uvicorn.error": {
                "handlers": ["default"],
                "level": settings.log_level.upper(),
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["uvicorn.access"],
                "level": "INFO",
                "propagate": False,
            },
        },
        "root": {
            "level": settings.log_level.upper(),
            "handlers": ["default"],
        },
    }
