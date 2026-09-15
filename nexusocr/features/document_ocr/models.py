"""
NexusOCR Document OCR Feature Models.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


class OCRStrategyType(str, Enum):
    TIER1_DIGITAL = "tier1_digital"
    TIER2_PADDLE_GPU = "tier2_paddle_gpu"
    FALLBACK_EMPTY = "fallback_empty"


class OCRPageDecision(BaseModel):
    page_number: int
    strategy: OCRStrategyType
    trust_score: float
    is_digital: bool
