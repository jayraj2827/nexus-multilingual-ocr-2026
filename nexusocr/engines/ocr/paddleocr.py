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
    Adaptive PP-OCRv6 Engine supporting NVIDIA CUDA, AMD ROCm, and optimized CPU execution.
    Lazy-loaded on first use to keep server startup fast.
    """

    def __init__(self) -> None:
        self._ocr = None
        self._initialized = False

    def _init(self) -> None:
        if self._initialized:
            return

        try:
            _stub_modelscope()
            from paddleocr import PaddleOCR
            from nexusocr.config import detect_hardware

            hw = detect_hardware()
            device_str = hw["device_type"]
            dev_name = hw["device_name"]

            print(f"[NexusOCR] [P3] Loading PaddleOCR v3.7 on {dev_name}...", flush=True)
            t0 = time.perf_counter()
            if device_str == "gpu":
                self._ocr = PaddleOCR(lang="en", device="gpu")
            else:
                self._ocr = PaddleOCR(
                    lang="en",
                    device="cpu",
                    enable_mkldnn=False,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                )
            self._initialized = True
            print(f"[NexusOCR] [P3] PaddleOCR ready on {dev_name} in {(time.perf_counter()-t0)*1000:.0f}ms [OK]", flush=True)

        except Exception as e:
            self._initialized = True
            print(f"[NexusOCR] [P3] PaddleOCR init error: {e}", flush=True)

    def is_available(self) -> bool:
        try:
            _stub_modelscope()
            import paddle
            return True
        except ImportError:
            return False

    def process_page_image(self, page_img: np.ndarray, page_num: int) -> Optional[PageResult]:
        """
        Extracts text from a scanned/image page using PaddleOCR on GPU or CPU.
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

        print(f"[NexusOCR] [P3: PaddleOCR] Page {page_num} ({w}x{h})...", flush=True)

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

            raw_items = []
            for idx, (t, s) in enumerate(zip(texts, scores or [1.0] * len(texts))):
                t_str = t.strip()
                if not t_str or (s is not None and s < 0.45):
                    continue

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

                if not box_coords:
                    box_coords = [0.0, float(idx * 20), float(w), float(idx * 20 + 18)]

                raw_items.append((box_coords, t_str, float(s) if s is not None else 1.0))

            if not raw_items:
                return None

            # Sort in human reading order: top-to-bottom line clusters, left-to-right
            # Line cluster threshold ~14px or 2.5% of height
            line_cluster_h = max(12.0, h * 0.02)
            raw_items.sort(key=lambda item: (round(item[0][1] / line_cluster_h) * line_cluster_h, item[0][0]))

            regions: List[ExtractedRegion] = []
            formatted_lines = []

            # Determine median line height to detect headings
            heights = [(b[3] - b[1]) for b, _, _ in raw_items if (b[3] - b[1]) > 5]
            median_h = float(np.median(heights)) if heights else 15.0

            for r_idx, (box_coords, t_str, score) in enumerate(raw_items):
                bh = box_coords[3] - box_coords[1]
                is_heading = (bh >= median_h * 1.35 and len(t_str) < 80) or (t_str.isupper() and len(t_str) < 60)
                category = "header" if is_heading else "text"

                regions.append(ExtractedRegion(
                    id=f"p{page_num}_ocr_{r_idx+1}",
                    bbox=BoundingBox(
                        xmin=box_coords[0],
                        ymin=box_coords[1],
                        xmax=box_coords[2],
                        ymax=box_coords[3]
                    ),
                    text=t_str,
                    category=category,
                    confidence=score,
                    source=ExtractionSource.DOCLING_LAYOUT
                ))

                if is_heading:
                    formatted_lines.append(f"### {t_str}")
                else:
                    formatted_lines.append(t_str)

            markdown_text = "\n\n".join(formatted_lines)

            print(
                f"[NexusOCR] [P3: PaddleOCR] Page {page_num} - "
                f"{len(formatted_lines)} lines, {len(regions)} boxes in {elapsed_ms:.1f}ms [OK]",
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
