"""
NexusOCR Base OCR Engine Contract.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional
import numpy as np

from nexusocr.contracts.results import PageResult


class BaseOCREngine(ABC):
    """Abstract interface for all OCR engine adapters."""

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the engine's required hardware/dependencies are ready."""
        pass

    @abstractmethod
    def process_page_image(self, page_img: np.ndarray, page_num: int) -> Optional[PageResult]:
        """Runs OCR on an image/raster array and returns PageResult."""
        pass
