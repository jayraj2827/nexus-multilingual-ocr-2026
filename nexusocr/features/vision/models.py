"""
NexusOCR Vision Feature Models.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VisualFeature(BaseModel):
    name: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VisionAnalysisResult(BaseModel):
    image_width: int
    image_height: int
    mean_brightness: float
    contrast_std: float
    features: List[VisualFeature] = Field(default_factory=list)
