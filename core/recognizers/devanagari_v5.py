"""
Devanagari / Hindi Text Recognizer using PP-OCRv5.
Supports Hindi, Marathi, Nepali, Sanskrit, and Devanagari-family languages.
"""

from typing import List, Tuple
import numpy as np
from core.recognizers.base import BaseRecognizer


class DevanagariV5Recognizer(BaseRecognizer):
    """Recognizes Devanagari/Hindi text lines."""

    def __init__(self, use_gpu: bool = False):
        self._engine = None
        self.use_gpu = use_gpu

    def _lazy_init(self):
        if self._engine is None:
            from paddleocr import PaddleOCR
            # PP-OCRv5 Devanagari multilingual model
            self._engine = PaddleOCR(
                use_angle_cls=False,
                lang="devanagari",
                use_gpu=self.use_gpu,
                show_log=False
            )

    @property
    def name(self) -> str:
        return "ppocr_v5_devanagari"

    def recognize_batch(self, crop_images: List[np.ndarray]) -> List[Tuple[str, float]]:
        if not crop_images:
            return []

        self._lazy_init()
        results = []

        for crop in crop_images:
            if crop.size == 0:
                results.append(("", 0.0))
                continue

            try:
                res = self._engine.ocr(crop, det=False, rec=True, cls=False)
                if res and res[0]:
                    text, conf = res[0][0]
                    results.append((text.strip(), float(conf)))
                else:
                    results.append(("", 0.0))
            except Exception:
                results.append(("", 0.0))

        return results
