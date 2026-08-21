"""
DBNet Text Detector wrapper for NexusOCR.
Language-agnostic text line boundary detection on full-page images.
"""

from typing import List, Tuple
import numpy as np
from core.types import BoundingBox


class DBNetDetector:
    """Detects text line bounding boxes using lightweight DBNet."""

    def __init__(self, use_gpu: bool = False):
        self._engine = None
        self.use_gpu = use_gpu

    def _lazy_init(self):
        if self._engine is None:
            from paddleocr import PaddleOCR
            # Mobile DBNet detector
            self._engine = PaddleOCR(
                use_angle_cls=False,
                det=True,
                rec=False,
                use_gpu=self.use_gpu,
                show_log=False
            )

    def detect_boxes(self, image: np.ndarray) -> List[Tuple[BoundingBox, np.ndarray]]:
        """
        Detects all text lines in the page image.
        Returns:
            List of (BoundingBox, cropped_image_patch)
        """
        if image is None or image.size == 0:
            return []

        self._lazy_init()
        h, w = image.shape[:2]

        try:
            results = self._engine.ocr(image, det=True, rec=False, cls=False)
        except Exception:
            return []

        detected = []
        if not results or not results[0]:
            return []

        for box in results[0]:
            pts = np.array(box, dtype=np.float32)
            xmin = float(max(0, np.min(pts[:, 0])))
            ymin = float(max(0, np.min(pts[:, 1])))
            xmax = float(min(w, np.max(pts[:, 0])))
            ymax = float(min(h, np.max(pts[:, 1])))

            if xmax <= xmin or ymax <= ymin:
                continue

            # Crop image patch
            crop = image[int(ymin):int(ymax), int(xmin):int(xmax)]
            polygon = pts.tolist()

            bbox = BoundingBox(
                xmin=xmin,
                ymin=ymin,
                xmax=xmax,
                ymax=ymax,
                polygon=polygon
            )
            detected.append((bbox, crop))

        # Sort top-to-bottom as initial layout ordering
        detected.sort(key=lambda item: item[0].ymin)
        return detected
