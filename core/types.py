"""
Data structures and Pydantic schemas for NexusOCR.
Following KISS principles: flat, explicit, and developer-friendly.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TextType(str, Enum):
    PRINTED = "printed"
    HANDWRITTEN = "handwritten"
    TABLE = "table"
    FIGURE = "figure"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ScriptType(str, Enum):
    LATIN = "latin"
    DEVANAGARI = "devanagari"
    GUJARATI = "gujarati"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class EngineType(str, Enum):
    NATIVE = "native_pdf"
    PPOCR_LATIN = "ppocr_v6_latin"
    PPOCR_DEVANAGARI = "ppocr_v5_devanagari"
    TESSERACT_GUJARATI = "tesseract_gujarati"
    PPOCR_HANDWRITING = "ppocr_v5_handwriting"
    FALLBACK_A_RETRY = "fallback_a_opencv_retry"
    FALLBACK_B_VLM = "fallback_b_paddleocr_vl"


class BoundingBox(BaseModel):
    """Normalized or pixel coordinates [xmin, ymin, xmax, ymax]."""
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    polygon: Optional[List[List[float]]] = None

    @property
    def width(self) -> float:
        return max(0.0, self.xmax - self.xmin)

    @property
    def height(self) -> float:
        return max(0.0, self.ymax - self.ymin)

    @property
    def area(self) -> float:
        return self.width * self.height


class ExtractedRegion(BaseModel):
    """Represents a single recognized text block or line."""
    id: str
    bbox: BoundingBox
    text: str
    raw_confidence: float = Field(ge=0.0, le=1.0)
    composite_confidence: float = Field(ge=0.0, le=1.0)
    script: ScriptType = ScriptType.UNKNOWN
    text_type: TextType = TextType.PRINTED
    engine_used: EngineType = EngineType.NATIVE
    is_retried: bool = False
    retry_pass_count: int = 0


class TableCell(BaseModel):
    row_idx: int
    col_idx: int
    row_span: int = 1
    col_span: int = 1
    text: str
    bbox: Optional[BoundingBox] = None


class TableStructure(BaseModel):
    """Represents an extracted tabular grid."""
    id: str
    bbox: BoundingBox
    html: str
    markdown: str
    num_rows: int
    num_cols: int
    cells: List[TableCell] = Field(default_factory=list)


class PageResult(BaseModel):
    """Complete extraction payload for a single PDF page."""
    page_number: int
    width: int
    height: int
    text_layer_trust_score: float = Field(ge=0.0, le=1.0)
    is_native_text: bool = False
    dominant_script: ScriptType = ScriptType.UNKNOWN
    regions: List[ExtractedRegion] = Field(default_factory=list)
    tables: List[TableStructure] = Field(default_factory=list)
    reading_order_markdown: str = ""
    structured_fields: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0
    vlm_escalated: bool = False


class DocumentResult(BaseModel):
    """Complete multi-page extraction result with global metadata."""
    file_name: str
    total_pages: int
    pages: List[PageResult] = Field(default_factory=list)
    full_markdown: str = ""
    structured_json: Dict[str, Any] = Field(default_factory=dict)
    average_trust_score: float = 0.0
    vlm_escalation_rate: float = 0.0
    total_execution_time_ms: float = 0.0
