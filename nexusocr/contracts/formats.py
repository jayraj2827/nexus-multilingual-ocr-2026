"""
NexusOCR Format Intelligence and Capability Contracts.
Defines supported document and image formats, extraction strategies, and media rejection policies.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

from nexusocr.exceptions import UnsupportedFormatError


class FormatCategory(str, Enum):
    PDF = "pdf"
    IMAGE = "image"
    DOCX = "docx"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    TEXT_MARKUP = "text_markup"
    EPUB = "epub"
    AUDIO_UNSUPPORTED = "audio_unsupported"
    VIDEO_UNSUPPORTED = "video_unsupported"
    UNKNOWN = "unknown"


class ExtractionMode(str, Enum):
    NATIVE_ONLY = "native_only"      # Direct digital parsing without neural OCR
    OCR_ONLY = "ocr_only"            # Pure neural OCR on raster image frames
    HYBRID = "hybrid"                # Tiered: Native text layer first, GPU OCR fallback / embedded image OCR
    UNSUPPORTED = "unsupported"      # Unsupported media types (audio, video, unknown)


class FormatCapability(BaseModel):
    """Represents technical extraction capabilities for a specific file format."""
    format_name: str
    extension: str
    category: FormatCategory
    extraction_mode: ExtractionMode
    can_native_text: bool = False
    can_ocr: bool = False
    can_extract_tables: bool = False
    can_render_pages: bool = False
    can_extract_metadata: bool = True
    can_extract_embedded_images: bool = False
    description: str = ""


# ── Format Definitions ────────────────────────────────────────────────────────

PDF_EXTENSIONS: Set[str] = {".pdf"}
IMAGE_EXTENSIONS: Set[str] = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".gif"}
DOCX_EXTENSIONS: Set[str] = {".docx"}
SPREADSHEET_EXTENSIONS: Set[str] = {".xlsx", ".csv", ".tsv"}
PRESENTATION_EXTENSIONS: Set[str] = {".pptx"}
TEXT_MARKUP_EXTENSIONS: Set[str] = {".txt", ".md", ".markdown", ".html", ".htm", ".xml"}
EPUB_EXTENSIONS: Set[str] = {".epub"}

AUDIO_EXTENSIONS: Set[str] = {
    ".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a", ".wma", ".aiff", ".opus"
}
VIDEO_EXTENSIONS: Set[str] = {
    ".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm", ".m4v", ".3gp"
}


class FormatResolver:
    """Resolves file paths to their technical format capabilities and extraction strategy."""

    @classmethod
    def get_extension(cls, path_or_name: str) -> str:
        p = Path(path_or_name)
        return p.suffix.lower()

    @classmethod
    def is_audio(cls, path_or_name: str) -> bool:
        return cls.get_extension(path_or_name) in AUDIO_EXTENSIONS

    @classmethod
    def is_video(cls, path_or_name: str) -> bool:
        return cls.get_extension(path_or_name) in VIDEO_EXTENSIONS

    @classmethod
    def is_supported(cls, path_or_name: str) -> bool:
        ext = cls.get_extension(path_or_name)
        return (
            ext in PDF_EXTENSIONS
            or ext in IMAGE_EXTENSIONS
            or ext in DOCX_EXTENSIONS
            or ext in SPREADSHEET_EXTENSIONS
            or ext in PRESENTATION_EXTENSIONS
            or ext in TEXT_MARKUP_EXTENSIONS
            or ext in EPUB_EXTENSIONS
        )

    @classmethod
    def resolve_capability(cls, path_or_name: str) -> FormatCapability:
        ext = cls.get_extension(path_or_name)

        if cls.is_audio(path_or_name):
            return FormatCapability(
                format_name="Audio Media",
                extension=ext,
                category=FormatCategory.AUDIO_UNSUPPORTED,
                extraction_mode=ExtractionMode.UNSUPPORTED,
                description="Audio files are not supported. NexusOCR is a document and image intelligence platform."
            )

        if cls.is_video(path_or_name):
            return FormatCapability(
                format_name="Video Media",
                extension=ext,
                category=FormatCategory.VIDEO_UNSUPPORTED,
                extraction_mode=ExtractionMode.UNSUPPORTED,
                description="Video files are not supported. NexusOCR is a document and image intelligence platform."
            )

        if ext in PDF_EXTENSIONS:
            return FormatCapability(
                format_name="Portable Document Format (PDF)",
                extension=ext,
                category=FormatCategory.PDF,
                extraction_mode=ExtractionMode.HYBRID,
                can_native_text=True,
                can_ocr=True,
                can_extract_tables=True,
                can_render_pages=True,
                can_extract_embedded_images=True,
                description="Digital vector text & table extraction with GPU neural OCR fallback for scanned pages."
            )

        if ext in IMAGE_EXTENSIONS:
            return FormatCapability(
                format_name="Raster / Multi-page Image",
                extension=ext,
                category=FormatCategory.IMAGE,
                extraction_mode=ExtractionMode.OCR_ONLY,
                can_native_text=False,
                can_ocr=True,
                can_extract_tables=False,
                can_render_pages=True,
                description="Frame-level visual neural OCR (PaddleOCR PP-OCRv6) with bounding box geometry."
            )

        if ext in DOCX_EXTENSIONS:
            return FormatCapability(
                format_name="Microsoft Word Document",
                extension=ext,
                category=FormatCategory.DOCX,
                extraction_mode=ExtractionMode.HYBRID,
                can_native_text=True,
                can_ocr=True,
                can_extract_tables=True,
                can_extract_embedded_images=True,
                description="Native paragraph hierarchy, heading levels, structured tables, and OCR on embedded images."
            )

        if ext in SPREADSHEET_EXTENSIONS:
            return FormatCapability(
                format_name="Spreadsheet / Tabular Data",
                extension=ext,
                category=FormatCategory.SPREADSHEET,
                extraction_mode=ExtractionMode.NATIVE_ONLY,
                can_native_text=True,
                can_extract_tables=True,
                description="Structured row/column matrix extraction, multi-sheet inspection, and clean Markdown tables."
            )

        if ext in PRESENTATION_EXTENSIONS:
            return FormatCapability(
                format_name="Presentation Slides",
                extension=ext,
                category=FormatCategory.PRESENTATION,
                extraction_mode=ExtractionMode.HYBRID,
                can_native_text=True,
                can_ocr=True,
                can_extract_tables=True,
                can_extract_embedded_images=True,
                description="Slide-by-slide titles, text frames, shape tables, and OCR on embedded visuals."
            )

        if ext in TEXT_MARKUP_EXTENSIONS:
            return FormatCapability(
                format_name="Plain Text / Markup Document",
                extension=ext,
                category=FormatCategory.TEXT_MARKUP,
                extraction_mode=ExtractionMode.NATIVE_ONLY,
                can_native_text=True,
                can_extract_tables=True,
                description="Direct structured text extraction with HTML table reconstruction and Markdown preservation."
            )

        if ext in EPUB_EXTENSIONS:
            return FormatCapability(
                format_name="Electronic Publication (EPUB)",
                extension=ext,
                category=FormatCategory.EPUB,
                extraction_mode=ExtractionMode.HYBRID,
                can_native_text=True,
                can_render_pages=True,
                description="Chapter-by-chapter digital text and layout extraction via PyMuPDF."
            )

        return FormatCapability(
            format_name="Unknown Format",
            extension=ext,
            category=FormatCategory.UNKNOWN,
            extraction_mode=ExtractionMode.UNSUPPORTED,
            description=f"File extension '{ext}' is not supported by NexusOCR."
        )

    @classmethod
    def validate_file(cls, path_or_name: str) -> FormatCapability:
        """
        Validates whether a file format is supported.
        Raises an explicit UnsupportedFormatError if audio, video, or unknown.
        """
        cap = cls.resolve_capability(path_or_name)
        if cap.category == FormatCategory.AUDIO_UNSUPPORTED:
            raise UnsupportedFormatError(
                path_or_name,
                f"Audio file '{cap.extension}' is not supported. NexusOCR is a document and image OCR intelligence system; audio and video processing is not supported."
            )
        if cap.category == FormatCategory.VIDEO_UNSUPPORTED:
            raise UnsupportedFormatError(
                path_or_name,
                f"Video file '{cap.extension}' is not supported. NexusOCR is a document and image OCR intelligence system; audio and video processing is not supported."
            )
        if not cls.is_supported(path_or_name):
            raise UnsupportedFormatError(
                path_or_name,
                f"Unsupported format '{cap.extension}'. NexusOCR supports PDF documents, images (PNG, JPG, TIFF, BMP, WebP), Office documents (DOCX, XLSX, PPTX), structured data (CSV), and text/markup (TXT, HTML, MD, EPUB)."
            )
        return cap

    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        all_exts = (
            sorted(list(PDF_EXTENSIONS))
            + sorted(list(IMAGE_EXTENSIONS))
            + sorted(list(DOCX_EXTENSIONS))
            + sorted(list(SPREADSHEET_EXTENSIONS))
            + sorted(list(PRESENTATION_EXTENSIONS))
            + sorted(list(TEXT_MARKUP_EXTENSIONS))
            + sorted(list(EPUB_EXTENSIONS))
        )
        return all_exts
