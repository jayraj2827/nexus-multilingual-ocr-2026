"""
NexusOCR Core Data Contracts and Result Schemas.
Pydantic schemas preserving exact field names, types, and defaults.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExtractionSource(str, Enum):
    DIGITAL_NATIVE = "digital_native"  # PyMuPDF fast text & table layer (<10ms)
    DOCLING_LAYOUT = "docling_layout"  # IBM Docling Layout & TableFormer
    OLLAMA_VLM = "ollama_vlm"          # Local Ollama Vision VLM (Qwen2.5-VL / Gemma)


class BoundingBox(BaseModel):
    xmin: float
    ymin: float
    xmax: float
    ymax: float

    @property
    def width(self) -> float:
        return max(0.0, self.xmax - self.xmin)

    @property
    def height(self) -> float:
        return max(0.0, self.ymax - self.ymin)


class ExtractedRegion(BaseModel):
    id: str
    bbox: BoundingBox
    text: str
    category: str = "text"  # 'title', 'header', 'text', 'table', 'figure', 'list_item'
    confidence: float = 1.0
    source: ExtractionSource = ExtractionSource.DIGITAL_NATIVE


class TableStructure(BaseModel):
    id: str
    bbox: BoundingBox
    num_rows: int
    num_cols: int
    markdown: str
    html: Optional[str] = ""


class PageResult(BaseModel):
    page_number: int
    width: int
    height: int
    is_digital: bool = True
    trust_score: float = 1.0
    regions: List[ExtractedRegion] = Field(default_factory=list)
    tables: List[TableStructure] = Field(default_factory=list)
    markdown: str = ""
    source: ExtractionSource = ExtractionSource.DIGITAL_NATIVE
    execution_time_ms: float = 0.0


class DocumentResult(BaseModel):
    file_name: str
    total_pages: int
    pages: List[PageResult] = Field(default_factory=list)
    full_markdown: str = ""
    structured_json: Dict[str, Any] = Field(default_factory=dict)
    average_trust_score: float = 1.0
    total_execution_time_ms: float = 0.0
