"""
NexusOCR Input Contracts and Processing Options.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProcessingOptions(BaseModel):
    """Execution options for document and media processing."""
    max_pages: Optional[int] = None
    dpi: int = 150
    trust_threshold: float = 0.85
    enable_ocr: bool = True
    enable_layout: bool = True
    enable_translation: bool = False
    target_language: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentInput(BaseModel):
    """Input payload describing a document for the pipeline."""
    file_path: str
    file_name: Optional[str] = None
    options: ProcessingOptions = Field(default_factory=ProcessingOptions)

    @property
    def name(self) -> str:
        return self.file_name or Path(self.file_path).name


class StageResult(BaseModel):
    """Outcome of a single pipeline stage execution."""
    stage_name: str
    status: StageStatus = StageStatus.PENDING
    execution_time_ms: float = 0.0
    output: Any = None
    error: Optional[str] = None
