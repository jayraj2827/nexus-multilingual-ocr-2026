"""
NexusOCR Core Exception Hierarchy.
Provides standard error classifications across pipeline stages and engines.
"""

from __future__ import annotations

from typing import Optional


class NexusOCRError(Exception):
    """Base exception for all NexusOCR errors."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(NexusOCRError):
    """Raised when configuration values are missing or invalid."""
    pass


class StageExecutionError(NexusOCRError):
    """Raised when a specific pipeline stage encounters a runtime failure."""

    def __init__(self, stage_name: str, message: str, original_exception: Optional[BaseException] = None) -> None:
        super().__init__(f"Stage '{stage_name}' failed: {message}")
        self.stage_name = stage_name
        self.original_exception = original_exception


class EngineUnavailableError(NexusOCRError):
    """Raised when an external engine (PaddleOCR, Docling, etc.) is requested but not available."""

    def __init__(self, engine_name: str, reason: str) -> None:
        super().__init__(f"Engine '{engine_name}' is unavailable: {reason}")
        self.engine_name = engine_name
        self.reason = reason


class UnsupportedFormatError(NexusOCRError):
    """Raised when input document or media format is not supported."""

    def __init__(self, file_path: str, format_name: str) -> None:
        super().__init__(f"Unsupported format '{format_name}' for file: {file_path}")
        self.file_path = file_path
        self.format_name = format_name


class ProcessingTimeoutError(NexusOCRError):
    """Raised when processing exceeds configured deadline."""
    pass
