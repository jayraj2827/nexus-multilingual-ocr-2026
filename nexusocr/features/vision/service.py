"""
NexusOCR Vision Feature Service.
Coordinates image processing, visual analysis, and preview generation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np

from nexusocr.contracts.results import BoundingBox
from nexusocr.engines.vision.base import BaseVisionEngine, DefaultVisionEngine
from nexusocr.features.vision.models import VisionAnalysisResult, VisualFeature
from nexusocr.processors.image import ImageProcessor


class VisionService:
    """Provides high-level computer vision and visual artifact operations."""

    def __init__(self, engine: Optional[BaseVisionEngine] = None) -> None:
        self.engine: BaseVisionEngine = engine or DefaultVisionEngine()

    def inspect_image(self, source: Union[str, Path, bytes, np.ndarray]) -> VisionAnalysisResult:
        """Loads and calculates visual metrics of an image."""
        img_np = ImageProcessor.load_image(source)
        analysis = self.engine.analyze_image(img_np)
        h, w = img_np.shape[:2]

        return VisionAnalysisResult(
            image_width=w,
            image_height=h,
            mean_brightness=analysis.get("mean_brightness", 0.0),
            contrast_std=analysis.get("std_contrast", 0.0),
            features=[
                VisualFeature(name="is_grayscale_like", score=1.0 if analysis.get("is_grayscale_like") else 0.0)
            ],
        )

    def crop_region(self, source: Union[str, Path, bytes, np.ndarray], bbox: BoundingBox) -> np.ndarray:
        """Crops a region given bounding box coordinates."""
        img_np = ImageProcessor.load_image(source)
        return ImageProcessor.crop_box(img_np, bbox)

    def generate_preview_jpeg(
        self,
        source: Union[str, Path, bytes, np.ndarray],
        max_width: int = 800,
        quality: int = 85
    ) -> bytes:
        """Generates a scaled JPEG preview for UI rendering."""
        img_np = ImageProcessor.load_image(source)
        scaled = ImageProcessor.resize_with_aspect_ratio(img_np, target_width=max_width)
        return ImageProcessor.to_jpeg_bytes(scaled, quality=quality)
