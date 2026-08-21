"""
Abstract base class for all pluggable OCR recognition engines in NexusOCR.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple
import numpy as np


class BaseRecognizer(ABC):
    """Abstract interface for script-specific and fallback OCR engines."""

    @abstractmethod
    def recognize_batch(self, crop_images: List[np.ndarray]) -> List[Tuple[str, float]]:
        """
        Processes a batch of line-level crop images.
        Returns:
            List of (recognized_text, confidence_score) where confidence is in [0.0, 1.0].
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Returns the name/identifier of this engine."""
        pass
