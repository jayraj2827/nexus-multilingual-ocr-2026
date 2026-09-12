"""
NexusOCR Layout Feature Models.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from nexusocr.contracts.results import BoundingBox, TableStructure


class LayoutElement(BaseModel):
    id: str
    bbox: BoundingBox
    element_type: str  # text, header, table, figure
    reading_order_idx: int
    content: str


class LayoutAnalysisResult(BaseModel):
    page_number: int
    elements: List[LayoutElement] = Field(default_factory=list)
    tables: List[TableStructure] = Field(default_factory=list)
