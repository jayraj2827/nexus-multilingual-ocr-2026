"""
NexusOCR Interfaces Package.
Exposes API, CLI, and SDK entry points.
"""

from __future__ import annotations

from nexusocr.interfaces.api import app, create_app
from nexusocr.interfaces.sdk import NexusOCRClient
from nexusocr.interfaces.cli import main

__all__ = ["app", "create_app", "NexusOCRClient", "main"]
