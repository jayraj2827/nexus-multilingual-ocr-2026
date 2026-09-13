"""
NexusOCR Image Media Processor.
Handles image conversions, multi-frame TIFFs, bounding-box cropping, resizing, and array normalization.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageSequence

from nexusocr.contracts.results import BoundingBox


class ImageProcessor:
    """Reusable technical image manipulation operations."""

    @staticmethod
    def load_image(source: Union[str, Path, bytes, np.ndarray]) -> np.ndarray:
        """Loads an image into an RGB NumPy array from filepath, bytes, or existing array."""
        if isinstance(source, np.ndarray):
            if len(source.shape) == 2:
                return cv2.cvtColor(source, cv2.COLOR_GRAY2RGB)
            if source.shape[2] == 4:
                return source[:, :, :3]
            return source

        if isinstance(source, (str, Path)):
            path_str = str(source)
            if not Path(path_str).exists():
                raise FileNotFoundError(f"Image not found: {path_str}")
            # Use Pillow to robustly support TIFF, WebP, BMP, etc.
            with Image.open(path_str) as img:
                return np.array(img.convert("RGB"))

        if isinstance(source, bytes):
            with Image.open(io.BytesIO(source)) as img_pil:
                return np.array(img_pil.convert("RGB"))

        raise TypeError(f"Unsupported image source type: {type(source)}")

    @staticmethod
    def load_multi_page_image(source: Union[str, Path, bytes]) -> List[np.ndarray]:
        """
        Loads single or multi-page image (e.g. multi-frame TIFF) as a list of RGB NumPy arrays.
        """
        frames: List[np.ndarray] = []
        if isinstance(source, bytes):
            stream = io.BytesIO(source)
            img = Image.open(stream)
        else:
            path_str = str(source)
            if not Path(path_str).exists():
                raise FileNotFoundError(f"Image not found: {path_str}")
            img = Image.open(path_str)

        try:
            for frame in ImageSequence.Iterator(img):
                frames.append(np.array(frame.convert("RGB")))
        finally:
            img.close()

        return frames if frames else [ImageProcessor.load_image(source)]

    @staticmethod
    def get_image_metadata(source: Union[str, Path, bytes, np.ndarray]) -> Dict[str, Union[int, str]]:
        """Extracts dimensions, format, and color channels."""
        if isinstance(source, np.ndarray):
            h, w = source.shape[:2]
            c = source.shape[2] if len(source.shape) > 2 else 1
            return {"width": w, "height": h, "channels": c, "format": "RAW"}

        if isinstance(source, bytes):
            with Image.open(io.BytesIO(source)) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format or "UNKNOWN",
                    "mode": img.mode,
                }

        path_str = str(source)
        with Image.open(path_str) as img:
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format or Path(path_str).suffix.upper().lstrip("."),
                "mode": img.mode,
            }

    @staticmethod
    def crop_box(image: np.ndarray, bbox: BoundingBox) -> np.ndarray:
        """Crops image region corresponding to a BoundingBox."""
        h, w = image.shape[:2]
        x0 = max(0, int(round(bbox.xmin)))
        y0 = max(0, int(round(bbox.ymin)))
        x1 = min(w, int(round(bbox.xmax)))
        y1 = min(h, int(round(bbox.ymax)))

        if x1 <= x0 or y1 <= y0:
            return np.zeros((0, 0, image.shape[2] if len(image.shape) > 2 else 1), dtype=image.dtype)
        return image[y0:y1, x0:x1]

    @staticmethod
    def resize_with_aspect_ratio(
        image: np.ndarray,
        target_width: Optional[int] = None,
        target_height: Optional[int] = None
    ) -> np.ndarray:
        """Resizes image preserving aspect ratio."""
        h, w = image.shape[:2]
        if target_width is None and target_height is None:
            return image

        if target_width is None:
            ratio = target_height / float(h)
            new_dim = (int(w * ratio), target_height)
        elif target_height is None:
            ratio = target_width / float(w)
            new_dim = (target_width, int(h * ratio))
        else:
            new_dim = (target_width, target_height)

        return cv2.resize(image, new_dim, interpolation=cv2.INTER_AREA)

    @staticmethod
    def to_jpeg_bytes(image: np.ndarray, quality: int = 90) -> bytes:
        """Encodes an RGB NumPy array to JPEG bytes."""
        img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        success, encoded = cv2.imencode(".jpg", img_bgr, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if not success:
            raise RuntimeError("Failed to encode image to JPEG")
        return encoded.tobytes()

    @staticmethod
    def detect_text_regions(image: np.ndarray) -> List[BoundingBox]:
        """
        Detects visual text line and paragraph bounding boxes via adaptive thresholding and morphological grouping.
        Works offline on CPU without heavy neural weights.
        """
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image

        # Adaptive threshold to isolate ink/text strokes
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        # Morphological kernel to merge horizontal characters into words and lines
        kernel_w = max(5, int(w * 0.025))
        kernel_h = max(2, int(h * 0.015))
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_w, kernel_h))
        dilated = cv2.dilate(thresh, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        raw_boxes: List[Tuple[int, int, int, int]] = []
        min_box_w = max(10, int(w * 0.015))
        min_box_h = max(8, int(h * 0.015))

        for c in contours:
            bx, by, bw, bh = cv2.boundingRect(c)
            if bw >= min_box_w and bh >= min_box_h and bw < w * 0.98:
                raw_boxes.append((bx, by, bw, bh))

        # Sort top-to-bottom, left-to-right
        line_band = max(15, int(h * 0.03))
        raw_boxes.sort(key=lambda b: (b[1] // line_band, b[0]))

        return [
            BoundingBox(
                xmin=float(bx),
                ymin=float(by),
                xmax=float(bx + bw),
                ymax=float(by + bh)
            )
            for bx, by, bw, bh in raw_boxes
        ]

    @staticmethod
    def describe_image(image: np.ndarray) -> Dict[str, Any]:
        """
        Extracts visual properties, layout characteristics, and generates a structured caption.
        """
        if image is None or image.size == 0:
            return {"caption": "Empty image", "width": 0, "height": 0}

        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image

        mean_brightness = float(np.mean(gray))
        contrast_std = float(np.std(gray))

        # Channel differential for color vs monochrome detection
        if len(image.shape) == 3:
            r, g, b = image[:, :, 0], image[:, :, 1], image[:, :, 2]
            color_diff = float(np.mean(np.abs(r.astype(float) - g.astype(float)) + np.abs(g.astype(float) - b.astype(float))))
            is_monochrome = color_diff < 8.0
        else:
            is_monochrome = True

        regions = ImageProcessor.detect_text_regions(image)
        has_text_content = len(regions) > 0

        # Build human-readable caption
        if has_text_content:
            doc_type = "Document / Scanned Page" if mean_brightness > 180 else "Visual Graphic / Signage"
            color_type = "Monochrome / Grayscale" if is_monochrome else "Full Color"
            caption = f"{doc_type} with {len(regions)} visual text region(s) [{color_type}, {w}x{h}px]"
        else:
            color_type = "Monochrome" if is_monochrome else "Color"
            caption = f"{color_type} Image ({w}x{h}px, Brightness: {mean_brightness:.0f})"

        return {
            "caption": caption,
            "width": w,
            "height": h,
            "mean_brightness": mean_brightness,
            "contrast_std": contrast_std,
            "is_monochrome": is_monochrome,
            "text_region_count": len(regions),
            "text_regions": regions,
        }
