"""
Gujarati Crop Recognizer using Tesseract 5 LSTM.
Operates on line-level crops using --psm 7 or --psm 8 (single line/word mode).
"""

from typing import List, Tuple
import numpy as np
import pytesseract
from PIL import Image
from core.recognizers.base import BaseRecognizer


class GujaratiTesseractRecognizer(BaseRecognizer):
    """Recognizes Gujarati text lines from cropped images."""

    def __init__(self, tesseract_cmd: str = None):
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
        self._config = "--psm 7 -l guj"

    @property
    def name(self) -> str:
        return "tesseract_gujarati"

    def recognize_batch(self, crop_images: List[np.ndarray]) -> List[Tuple[str, float]]:
        if not crop_images:
            return []

        results = []
        for crop in crop_images:
            if crop.size == 0:
                results.append(("", 0.0))
                continue

            try:
                pil_img = Image.fromarray(crop)
                # Extract text and data dictionary for confidence
                data = pytesseract.image_to_data(pil_img, config=self._config, output_type=pytesseract.Output.DICT)
                
                texts = []
                confs = []
                for i, text in enumerate(data.get("text", [])):
                    if text.strip():
                        texts.append(text.strip())
                        try:
                            conf_val = float(data["conf"][i])
                            if conf_val >= 0:
                                confs.append(conf_val / 100.0)
                        except (ValueError, TypeError):
                            pass

                full_text = " ".join(texts).strip()
                avg_conf = sum(confs) / len(confs) if confs else 0.70
                results.append((full_text, avg_conf))
            except Exception:
                # If tesseract guj data isn't installed locally, return placeholder with lower confidence
                results.append(("", 0.0))

        return results
