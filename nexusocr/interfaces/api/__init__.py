"""
NexusOCR API Interface Package.
"""

from __future__ import annotations

from nexusocr.interfaces.api.app import app, create_app
from nexusocr.interfaces.api.routes import router

__all__ = ["app", "create_app", "router"]
