"""
NexusOCR Image Media Processor.
Handles image conversions, bounding-box cropping, resizing, and array normalization.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

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
            img_bgr = cv2.imread(path_str)
            if img_bgr is None:
                raise ValueError(f"Failed to read image file: {path_str}")
            return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        if isinstance(source, bytes):
            img_pil = Image.open(io.BytesIO(source)).convert("RGB")
            return np.array(img_pil)

        raise TypeError(f"Unsupported image source type: {type(source)}")

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
