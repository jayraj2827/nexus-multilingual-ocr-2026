"""
Pillar 3: PaddleOCR v3.7 Engine (PP-OCRv6 on CUDA GPU).

Uses PaddleOCR backed by paddlepaddle-gpu for RTX 4060 CUDA inference.
- Speed:    ~150ms/page (GPU warm), ~1.5s first page (model load)
- Accuracy: 0.99–1.00 confidence on clean scanned documents
- Languages: 80+ including Hindi, Gujarati, Arabic, Chinese, Japanese, Korean
"""

import sys
import types
import time
import logging
from typing import Optional

import cv2
import numpy as np

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from engine.types import PageResult, ExtractionSource
import config

logging.getLogger("ppocr").setLevel(logging.WARNING)


def _stub_modelscope():
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


class PaddleOCREngine:
    """
    PaddleOCR PP-OCRv6 Engine on CUDA (RTX 4060).
    Lazy-loaded on first use to keep server startup fast.
    """

    def __init__(self):
        self._ocr = None
        self._initialized = False

    def _init(self):
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
            return paddle.is_compiled_with_cuda()
        except ImportError:
            return False

    def process_page_image(self, page_img: np.ndarray, page_num: int) -> Optional[PageResult]:
        """
        Extracts text from a scanned/image page using PaddleOCR on GPU.
        Returns a PageResult with clean Markdown text.
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

            if not texts:
                print(f"[NexusOCR] [P3] No text detected on Page {page_num}.", flush=True)
                return None

            # Filter low-confidence lines (< 0.6)
            lines = [
                t.strip()
                for t, s in zip(texts, scores or [1.0] * len(texts))
                if t.strip() and (s is None or s >= 0.6)
            ]
            markdown_text = "\n".join(lines)

            print(
                f"[NexusOCR] [P3: PaddleOCR GPU] Page {page_num} - "
                f"{len(lines)} lines in {elapsed_ms:.1f}ms [OK]",
                flush=True
            )

            return PageResult(
                page_number=page_num,
                width=w,
                height=h,
                is_digital=False,
                trust_score=0.95,
                markdown=markdown_text,
                source=ExtractionSource.DOCLING_LAYOUT,
                execution_time_ms=elapsed_ms,
            )

        except Exception as e:
            print(f"[NexusOCR] [P3] PaddleOCR exception on Page {page_num}: {e}", flush=True)
            return None
