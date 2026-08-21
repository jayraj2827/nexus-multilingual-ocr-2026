"""
Latin / English Text Recognizer using PP-OCRv6 (SVTR-LCNet architecture).
"""

from typing import List, Tuple
import numpy as np
from core.recognizers.base import BaseRecognizer


class LatinV6Recognizer(BaseRecognizer):
    """Recognizes English and Latin-script text lines."""

    def __init__(self, use_gpu: bool = False):
        self._engine = None
        self.use_gpu = use_gpu

    def _lazy_init(self):
        if self._engine is None:
            from paddleocr import PaddleOCR
            # PP-OCRv6 English / Latin recognition
            self._engine = PaddleOCR(
                use_angle_cls=False,
                lang="en",
                use_gpu=self.use_gpu,
                show_log=False
            )

    @property
    def name(self) -> str:
        return "ppocr_v6_latin"

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
                # Run OCR recognition only on the line crop
                res = self._engine.ocr(crop, det=False, rec=True, cls=False)
                if res and res[0]:
                    text, conf = res[0][0]
                    results.append((text.strip(), float(conf)))
                else:
                    results.append(("", 0.0))
            except Exception:
                results.append(("", 0.0))

        return results
