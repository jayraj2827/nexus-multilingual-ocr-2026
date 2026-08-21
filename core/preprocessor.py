"""
Image preprocessing and PDF rasterization for NexusOCR.
Handles auto-deskewing, contrast normalization, Sauvola binarization, and DPI scaling.
"""

import cv2
import numpy as np
from PIL import Image
import fitz  # PyMuPDF
from typing import Tuple, Optional
import config


def rasterize_pdf_page(page: fitz.Page, dpi: int = config.BASE_RASTER_DPI) -> np.ndarray:
    """
    Renders a PyMuPDF page to an RGB NumPy array at the specified DPI.
    """
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
    return img


def deskew_image(image: np.ndarray, max_angle: float = 45.0) -> Tuple[np.ndarray, float]:
    """
    Detects text skew angle using image contours / minAreaRect and rotates to 0 degrees.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image.copy()

    # Invert and threshold to get text pixels
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Find all foreground pixels
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 50:
        return image, 0.0

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) > max_angle or abs(angle) < 0.3:
        return image, 0.0

    # Rotate the image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    return rotated, angle


def enhance_crop_for_retry(crop_img: np.ndarray) -> np.ndarray:
    """
    Applies aggressive contrast normalization, sharpening, and adaptive binarization
    for Fallback A (low-confidence crop retry).
    """
    if crop_img.size == 0:
        return crop_img

    if len(crop_img.shape) == 3:
        gray = cv2.cvtColor(crop_img, cv2.COLOR_RGB2GRAY)
    else:
        gray = crop_img.copy()

    # Contrast Stretching (Histogram Equalization via CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Adaptive Threshold (Sauvola approximation using Gaussian adaptive threshold)
    binary = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 8
    )

    # Convert back to RGB for recognizer inputs
    result_rgb = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)
    return result_rgb


def calculate_image_quality(image: np.ndarray) -> float:
    """
    Computes a normalized contrast & sharpness metric in [0.0, 1.0].
    Uses Laplacian variance.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image

    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # Normalize: variance > 500 is very sharp (1.0), variance < 50 is blurry (0.1)
    normalized = min(1.0, max(0.1, laplacian_var / 500.0))
    return float(normalized)
