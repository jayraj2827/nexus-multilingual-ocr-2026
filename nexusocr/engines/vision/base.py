"""
NexusOCR Vision Engine Base & Adapters.
Handles image inspection, visual brightness/contrast profiling, and region clustering.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import numpy as np

from nexusocr.contracts.results import BoundingBox


class BaseVisionEngine(ABC):
    """Abstract interface for computer vision engine adapters."""

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    def analyze_image(self, image: np.ndarray) -> Dict[str, Any]:
        pass


class DefaultVisionEngine(BaseVisionEngine):
    """Standard computer vision analyzer using OpenCV and NumPy."""

    def is_available(self) -> bool:
        return True

    def analyze_image(self, image: np.ndarray) -> Dict[str, Any]:
        """Calculates image dimensions, mean brightness, contrast, and color distribution."""
        if image is None or image.size == 0:
            return {"valid": False}

        h, w = image.shape[:2]
        mean_brightness = float(np.mean(image))
        std_contrast = float(np.std(image))

        # Detect whether image is largely black & white or colored
        is_grayscale_like = False
        if len(image.shape) == 3 and image.shape[2] >= 3:
            diff_rg = np.mean(np.abs(image[:, :, 0].astype(float) - image[:, :, 1].astype(float)))
            diff_gb = np.mean(np.abs(image[:, :, 1].astype(float) - image[:, :, 2].astype(float)))
            is_grayscale_like = (diff_rg < 5.0) and (diff_gb < 5.0)

        return {
            "valid": True,
            "width": w,
            "height": h,
            "channels": image.shape[2] if len(image.shape) > 2 else 1,
            "mean_brightness": mean_brightness,
            "std_contrast": std_contrast,
            "is_grayscale_like": is_grayscale_like,
        }
