"""
NexusOCR PDF Media Processor.
Handles low-level PDF document access, rasterization, page rendering, and metrics via PyMuPDF.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator, List, Optional, Tuple

import fitz  # PyMuPDF
import numpy as np


class PDFProcessor:
    """Reusable PDF document loading, rendering, and rasterization operations."""

    @staticmethod
    def open_document(file_path: str) -> fitz.Document:
        """Opens and returns a PyMuPDF Document object."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        return fitz.open(file_path)

    @staticmethod
    def get_page_count(file_path: str) -> int:
        """Returns total pages in a PDF document."""
        with fitz.open(file_path) as doc:
            return len(doc)

    @staticmethod
    def render_page_to_pixmap(page: fitz.Page, dpi: int = 150) -> fitz.Pixmap:
        """Renders a PDF page to a PyMuPDF Pixmap at specified DPI."""
        return page.get_pixmap(dpi=dpi)

    @classmethod
    def render_page_to_numpy(cls, page: fitz.Page, dpi: int = 150) -> np.ndarray:
        """Renders a PDF page directly into an RGB uint8 NumPy array."""
        pix = cls.render_page_to_pixmap(page, dpi=dpi)
        img_np = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
        if pix.n == 4:
            # Drop alpha channel if present
            img_np = img_np[:, :, :3]
        return img_np

    @classmethod
    def render_page_to_jpeg_bytes(cls, page: fitz.Page, dpi: int = 150) -> bytes:
        """Renders a single PDF page directly to JPEG bytes."""
        pix = cls.render_page_to_pixmap(page, dpi=dpi)
        return pix.tobytes("jpeg")

    @classmethod
    def iterate_pages(
        cls,
        file_path: str,
        max_pages: Optional[int] = None
    ) -> Generator[Tuple[int, fitz.Page], None, None]:
        """Yields (page_number, page_object) up to max_pages."""
        doc = cls.open_document(file_path)
        total = len(doc)
        limit = min(total, max_pages) if max_pages else total
        try:
            for idx in range(limit):
                yield idx + 1, doc[idx]
        finally:
            doc.close()
