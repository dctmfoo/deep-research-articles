# File: logger.py | Module: mcp-server
"""Configurable logging for Deep Research Articles pipeline.

Enable debug logging via environment variable:
    export DR_DEBUG=1           # Enable debug mode
    export DR_LOG_LEVEL=DEBUG   # Set log level (DEBUG, INFO, WARNING, ERROR)
    export DR_LOG_FILE=/path/to/file.log  # Log to file (optional)
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class PipelineLogger:
    """Configurable logger for the research pipeline."""

    _instance: PipelineLogger | None = None
    _logger: logging.Logger

    def __new__(cls) -> PipelineLogger:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup_logger()
        return cls._instance

    def _setup_logger(self) -> None:
        """Configure the logger based on environment variables."""
        self._logger = logging.getLogger("deep-research")

        # Prevent duplicate handlers on reload
        self._logger.handlers.clear()

        # Check if debug mode is enabled
        debug_enabled = os.environ.get("DR_DEBUG", "").lower() in ("1", "true", "yes")

        # Get log level from env or default based on debug mode
        level_name = os.environ.get("DR_LOG_LEVEL", "DEBUG" if debug_enabled else "INFO")
        level = getattr(logging, level_name.upper(), logging.INFO)
        self._logger.setLevel(level)

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler (only if debug enabled or explicitly requested)
        if debug_enabled or os.environ.get("DR_LOG_CONSOLE", "").lower() in ("1", "true"):
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            self._logger.addHandler(console_handler)

        # File handler (if path specified)
        log_file = os.environ.get("DR_LOG_FILE", "")
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self._logger.addHandler(file_handler)

        # If no handlers added, add a null handler to prevent warnings
        if not self._logger.handlers:
            self._logger.addHandler(logging.NullHandler())

    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled."""
        return self._logger.level <= logging.DEBUG

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message."""
        self._logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message."""
        self._logger.error(msg, **kwargs)

    def exception(self, msg: str, **kwargs: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(msg, **kwargs)

    def phase_start(self, phase: str, details: str = "") -> None:
        """Log start of a pipeline phase."""
        self.info(f"[PHASE START] {phase}" + (f": {details}" if details else ""))

    def phase_end(self, phase: str, success: bool = True, details: str = "") -> None:
        """Log end of a pipeline phase."""
        status = "SUCCESS" if success else "FAILED"
        self.info(f"[PHASE {status}] {phase}" + (f": {details}" if details else ""))

    def api_call(self, service: str, method: str, **params: Any) -> None:
        """Log API call (debug level)."""
        param_str = ", ".join(f"{k}={v}" for k, v in params.items())
        self.debug(f"[API] {service}.{method}({param_str})")

    def api_response(self, service: str, method: str, duration_ms: float, success: bool = True) -> None:
        """Log API response (debug level)."""
        status = "OK" if success else "ERROR"
        self.debug(f"[API] {service}.{method} -> {status} ({duration_ms:.0f}ms)")

    def progress(self, phase: str, percent: int, message: str = "") -> None:
        """Log progress update."""
        self.info(f"[PROGRESS] {phase}: {percent}%" + (f" - {message}" if message else ""))


# Singleton instance
logger = PipelineLogger()


# Convenience functions for direct import
def debug(msg: str, **kwargs: Any) -> None:
    logger.debug(msg, **kwargs)

def info(msg: str, **kwargs: Any) -> None:
    logger.info(msg, **kwargs)

def warning(msg: str, **kwargs: Any) -> None:
    logger.warning(msg, **kwargs)

def error(msg: str, **kwargs: Any) -> None:
    logger.error(msg, **kwargs)

def exception(msg: str, **kwargs: Any) -> None:
    logger.exception(msg, **kwargs)
