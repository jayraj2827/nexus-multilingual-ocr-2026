"""
NexusOCR Output Formatting and Response Serialization Contracts.
"""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, Field

from nexusocr.contracts.results import DocumentResult, PageResult


class PipelineSummary(BaseModel):
    """Execution summary statistics across pipeline stages."""
    file_name: str
    total_pages: int
    stages_executed: List[str] = Field(default_factory=list)
    stage_latencies_ms: Dict[str, float] = Field(default_factory=dict)
    total_latency_ms: float = 0.0
    success: bool = True
    error_message: str = ""


def format_document_json(result: DocumentResult) -> Dict[str, Any]:
    """Serializes DocumentResult into standard API-compatible structured JSON."""
    return result.model_dump()
