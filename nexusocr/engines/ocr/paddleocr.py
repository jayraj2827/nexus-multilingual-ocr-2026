"""
Pillar 3: PaddleOCR v3.7 Engine (PP-OCRv6 on CUDA GPU).

Uses PaddleOCR backed by paddlepaddle-gpu for RTX 4060 CUDA inference.
- Speed:    ~150ms/page (GPU warm), ~1.5s first page (model load)
- Accuracy: 0.99–1.00 confidence on clean scanned documents
- Languages: 80+ including Hindi, Gujarati, Arabic, Chinese, Japanese, Korean
"""

from __future__ import annotations

import logging
import sys
import time
import types
from typing import List, Optional

import cv2
import numpy as np

from nexusocr.contracts.results import (
    BoundingBox,
    ExtractedRegion,
    ExtractionSource,
    PageResult,
)
from nexusocr.engines.ocr.base import BaseOCREngine
import nexusocr.config as config

logging.getLogger("ppocr").setLevel(logging.WARNING)


def _stub_modelscope() -> None:
    """
    Stub out modelscope before paddleocr/paddlex imports it.
    modelscope is only needed for Alibaba ModelScope hub downloads —
    all models are already cached in .paddlex/official_models/, safe to skip.
    """
    for mod in [
        "modelscope", "modelscope.utils", "modelscope.utils.import_utils",
        "modelscope.utils.ast_utils", "modelscope.utils.file_utils",
        "modelscope.utils.logger", "modelscope.utils.torch_utils",
    ]:
        if mod not in sys.modules:
            sys.modules[mod] = types.ModuleType(mod)


class PaddleOCREngine(BaseOCREngine):
    """
    PaddleOCR PP-OCRv6 Engine on CUDA (RTX 4060).
    Lazy-loaded on first use to keep server startup fast.
    """

    def __init__(self) -> None:
        self._ocr = None
        self._initialized = False

    def _init(self) -> None:
        if self._initialized:
            return

        try:
            import paddle
            if not paddle.is_compiled_with_cuda() or paddle.device.cuda.device_count() == 0:
                print("[NexusOCR] [P3] paddlepaddle-gpu not detected - visual OCR disabled.", flush=True)
                self._initialized = True
                return

            _stub_modelscope()
            from paddleocr import PaddleOCR

            print("[NexusOCR] [P3] Loading PaddleOCR v3.7 (PP-OCRv6) on RTX 4060...", flush=True)
            t0 = time.perf_counter()
            self._ocr = PaddleOCR(lang="en", device="gpu")
            self._initialized = True
            print(f"[NexusOCR] [P3] PaddleOCR GPU ready in {(time.perf_counter()-t0)*1000:.0f}ms [OK]", flush=True)

        except Exception as e:
            self._initialized = True
            print(f"[NexusOCR] [P3] PaddleOCR init error: {e}", flush=True)

    def is_available(self) -> bool:
        try:
            import paddle
            return bool(paddle.is_compiled_with_cuda())
        except ImportError:
            return False

    def process_page_image(self, page_img: np.ndarray, page_num: int) -> Optional[PageResult]:
        """
        Extracts text from a scanned/image page using PaddleOCR on GPU.
        Returns a PageResult with clean Markdown text and bounding boxes.
        """
        if page_img is None or page_img.size == 0:
            return None

        self._init()

        if self._ocr is None:
            print(f"[NexusOCR] [P3] PaddleOCR not available for Page {page_num}.", flush=True)
            return None

        start = time.perf_counter()
        h, w = page_img.shape[:2]

        print(f"[NexusOCR] [P3: PaddleOCR GPU] Page {page_num} ({w}x{h})...", flush=True)

        try:
            result = self._ocr.predict(page_img)
            elapsed_ms = (time.perf_counter() - start) * 1000.0

            if not result:
                return None

            r = result[0]
            texts = r.get("rec_texts", [])
            scores = r.get("rec_scores", [])
            boxes = r.get("rec_boxes", [])
            dt_polys = r.get("dt_polys", [])

            if not texts:
                print(f"[NexusOCR] [P3] No text detected on Page {page_num}.", flush=True)
                return None

            regions: List[ExtractedRegion] = []
            clean_lines = []

            for idx, (t, s) in enumerate(zip(texts, scores or [1.0] * len(texts))):
                t_str = t.strip()
                if not t_str or (s is not None and s < 0.5):
                    continue

                clean_lines.append(t_str)

                # Extract bounding box from rec_boxes or dt_polys
                box_coords = None
                if idx < len(boxes) and boxes[idx] is not None:
                    b = boxes[idx]
                    if len(b) >= 4:
                        box_coords = [float(b[0]), float(b[1]), float(b[2]), float(b[3])]
                elif idx < len(dt_polys) and dt_polys[idx] is not None:
                    pts = np.array(dt_polys[idx])
                    if len(pts) > 0:
                        xmin = float(np.min(pts[:, 0]))
                        ymin = float(np.min(pts[:, 1]))
                        xmax = float(np.max(pts[:, 0]))
                        ymax = float(np.max(pts[:, 1]))
                        box_coords = [xmin, ymin, xmax, ymax]

                if box_coords:
                    regions.append(ExtractedRegion(
                        id=f"p{page_num}_ocr_{idx}",
                        bbox=BoundingBox(
                            xmin=box_coords[0],
                            ymin=box_coords[1],
                            xmax=box_coords[2],
                            ymax=box_coords[3]
                        ),
                        text=t_str,
                        category="text",
                        confidence=float(s) if s is not None else 1.0,
                        source=ExtractionSource.DOCLING_LAYOUT
                    ))

            markdown_text = "\n\n".join(clean_lines)

            print(
                f"[NexusOCR] [P3: PaddleOCR GPU] Page {page_num} - "
                f"{len(clean_lines)} lines, {len(regions)} boxes in {elapsed_ms:.1f}ms [OK]",
                flush=True
            )

            return PageResult(
                page_number=page_num,
                width=w,
                height=h,
                is_digital=False,
                trust_score=0.95,
                regions=regions,
                markdown=markdown_text,
                source=ExtractionSource.DOCLING_LAYOUT,
                execution_time_ms=elapsed_ms,
            )

        except Exception as e:
            print(f"[NexusOCR] [P3] PaddleOCR exception on Page {page_num}: {e}", flush=True)
            return None
