"""
NexusOCR Unified Logging Infrastructure.
Preserves existing console conventions while supporting structured stage logging.
"""

from __future__ import annotations

import logging
import sys
from typing import Optional


# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def log(msg: str) -> None:
    """Print console log message with flush=True, preserving existing pipeline logs."""
    print(msg, flush=True)


class NexusLogger:
    """Logger wrapper providing structured stage and engine diagnostics."""

    def __init__(self, name: str = "NexusOCR") -> None:
        self.name = name
        self._logger = logging.getLogger(name)

    def info(self, msg: str) -> None:
        log(f"[{self.name}] {msg}")

    def warning(self, msg: str) -> None:
        log(f"[{self.name}] [Warning] {msg}")

    def error(self, msg: str, exc: Optional[BaseException] = None) -> None:
        log(f"[{self.name}] [Error] {msg}")
        if exc is not None:
            self._logger.error(msg, exc_info=exc)

    def debug(self, msg: str) -> None:
        self._logger.debug(f"[{self.name}] [Debug] {msg}")


# Default logger instance
logger = NexusLogger("NexusOCR")
