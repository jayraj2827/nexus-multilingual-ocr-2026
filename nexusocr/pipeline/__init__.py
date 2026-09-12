"""
NexusOCR Pipeline Runtime Package.
Exports runner, context, stage, and execution utilities.
"""

from __future__ import annotations

from nexusocr.pipeline.context import ProcessingContext
from nexusocr.pipeline.stage import PipelineStage
from nexusocr.pipeline.execution import StageExecutor
from nexusocr.pipeline.runner import PipelineRunner

__all__ = [
    "ProcessingContext",
    "PipelineStage",
    "StageExecutor",
    "PipelineRunner",
]
