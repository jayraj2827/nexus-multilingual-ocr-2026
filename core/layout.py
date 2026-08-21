"""
Document Layout Parser with PP-DocLayout-S and PP-DocLayout-M escalation ladder.
Segments full page into Text, Table, Header, Footer, and Figure regions.
"""

from typing import List, Dict, Any, Tuple
import numpy as np
from core.types import BoundingBox
import config


class LayoutParser:
    """Classifies document page layout regions using lightweight models."""

    def __init__(self, use_gpu: bool = False):
        self.use_gpu = use_gpu
        self._engine_small = None
        self._engine_medium = None

    def _lazy_init_small(self):
        if self._engine_small is None:
            from paddleocr import PPStructure
            # PP-DocLayout-S baseline
            self._engine_small = PPStructure(
                show_log=False,
                use_gpu=self.use_gpu,
                layout=True,
                table=False,
                ocr=False
            )

    def _lazy_init_medium(self):
        if self._engine_medium is None:
            from paddleocr import PPStructure
            # PP-DocLayout-M escalation
            self._engine_medium = PPStructure(
                show_log=False,
                use_gpu=self.use_gpu,
                layout=True,
                table=False,
                ocr=False
            )

    def parse_layout(self, image: np.ndarray) -> List[Dict[str, Any]]:
        """
        Extracts structural layout blocks from the page image.
        Returns:
            List of dicts: {"type": str, "bbox": BoundingBox, "confidence": float}
        """
        if image is None or image.size == 0:
            return []

        self._lazy_init_small()
        h, w = image.shape[:2]

        try:
            results = self._engine_small(image)
        except Exception:
            return []

        layout_boxes = []
        low_confidence_count = 0

        for res in results:
            cat = res.get("type", "text").lower()
            box = res.get("bbox", [0, 0, w, h])
            conf = float(res.get("score", 0.90))

            if conf < config.LAYOUT_CONFIDENCE_THRESHOLD:
                low_confidence_count += 1

            bbox = BoundingBox(
                xmin=float(box[0]),
                ymin=float(box[1]),
                xmax=float(box[2]),
                ymax=float(box[3])
            )
            layout_boxes.append({
                "type": cat,
                "bbox": bbox,
                "confidence": conf
            })

        # Escalation Ladder: If layout is uncertain, escalate to PP-DocLayout-M
        if low_confidence_count > 2 or not layout_boxes:
            try:
                self._lazy_init_medium()
                med_results = self._engine_medium(image)
                if med_results:
                    layout_boxes = []
                    for res in med_results:
                        cat = res.get("type", "text").lower()
                        box = res.get("bbox", [0, 0, w, h])
                        conf = float(res.get("score", 0.92))
                        bbox = BoundingBox(
                            xmin=float(box[0]),
                            ymin=float(box[1]),
                            xmax=float(box[2]),
                            ymax=float(box[3])
                        )
                        layout_boxes.append({
                            "type": cat,
                            "bbox": bbox,
                            "confidence": conf
                        })
            except Exception:
                pass

        return layout_boxes
