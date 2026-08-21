"""
Text-Type and Script Router with Hierarchical Grouped Batching.
Classifies crops into (Latin, Devanagari, Gujarati, Handwritten) and groups them
to eliminate per-crop loop overhead.
"""

from typing import List, Tuple, Dict
import numpy as np
import cv2
from core.types import ScriptType, TextType, BoundingBox


class DifficultyRouter:
    """Classifies crops and builds grouped batches for recognizers."""

    def classify_crop_script(self, crop: np.ndarray) -> ScriptType:
        """
        Lightweight script classification on a cropped line image.
        Uses stroke density, baseline characteristics, and top-line (shirorekha) detection.
        """
        if crop is None or crop.size == 0:
            return ScriptType.LATIN

        if len(crop.shape) == 3:
            gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
        else:
            gray = crop

        h, w = gray.shape
        if h < 5 or w < 5:
            return ScriptType.LATIN

        # Binarize
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        # 1. Shirorekha (Top Horizontal Continuous Line) Detection for Devanagari (Hindi)
        # Devanagari text has a strong continuous horizontal line near the top 20-35% of the line height
        upper_band = thresh[int(h * 0.15):int(h * 0.40), :]
        horizontal_projection = np.sum(upper_band, axis=1) / (w * 255.0)
        max_upper_density = np.max(horizontal_projection) if len(horizontal_projection) > 0 else 0.0

        if max_upper_density > 0.65:
            return ScriptType.DEVANAGARI

        # 2. Gujarati Script Check (Lack of Shirorekha + high loop density)
        # Gujarati looks similar to Devanagari but lacks the continuous top line
        mid_band = thresh[int(h * 0.40):int(h * 0.70), :]
        mid_projection = np.sum(mid_band, axis=1) / (w * 255.0)
        max_mid_density = np.max(mid_projection) if len(mid_projection) > 0 else 0.0

        if max_upper_density < 0.45 and max_mid_density > 0.50:
            # Check aspect ratios / loops
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if len(contours) > 3:
                return ScriptType.GUJARATI

        # Default to Latin for standard horizontal lines without distinct Indic features
        return ScriptType.LATIN

    def classify_crop_text_type(self, crop: np.ndarray) -> TextType:
        """
        Classifies whether a crop is printed vs. handwritten based on stroke variance.
        """
        if crop is None or crop.size == 0:
            return TextType.PRINTED

        if len(crop.shape) == 3:
            gray = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
        else:
            gray = crop

        # Stroke angle and line thickness variance is higher in handwriting
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=20, minLineLength=10, maxLineGap=3)

        if lines is not None and len(lines) > 0:
            angles = []
            for l in lines:
                x1, y1, x2, y2 = l[0]
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                angles.append(abs(angle))

            # High angle variance indicates handwriting / cursive text
            if len(angles) >= 4 and np.std(angles) > 35.0:
                return TextType.HANDWRITTEN

        return TextType.PRINTED

    def build_grouped_batches(
        self,
        detected_items: List[Tuple[BoundingBox, np.ndarray]]
    ) -> Dict[str, List[Tuple[int, BoundingBox, np.ndarray, ScriptType, TextType]]]:
        """
        Groups detected crops by target recognizer key:
        'latin', 'devanagari', 'gujarati', 'handwriting'.
        Returns dict of item tuples preserving original index for deterministic reassembly.
        """
        batches = {
            "latin": [],
            "devanagari": [],
            "gujarati": [],
            "handwriting": []
        }

        if not detected_items:
            return batches

        # Sample 5 items to check if page is homogeneous Latin
        sample_indices = np.linspace(0, len(detected_items) - 1, min(5, len(detected_items)), dtype=int)
        sample_scripts = [self.classify_crop_script(detected_items[idx][1]) for idx in sample_indices]
        sample_types = [self.classify_crop_text_type(detected_items[idx][1]) for idx in sample_indices]

        is_homogeneous_latin = all(s == ScriptType.LATIN for s in sample_scripts) and all(t == TextType.PRINTED for t in sample_types)

        for idx, (bbox, crop) in enumerate(detected_items):
            if is_homogeneous_latin:
                batches["latin"].append((idx, bbox, crop, ScriptType.LATIN, TextType.PRINTED))
                continue

            text_type = self.classify_crop_text_type(crop)
            if text_type == TextType.HANDWRITTEN:
                batches["handwriting"].append((idx, bbox, crop, ScriptType.LATIN, TextType.HANDWRITTEN))
                continue

            script = self.classify_crop_script(crop)
            if script == ScriptType.DEVANAGARI:
                batches["devanagari"].append((idx, bbox, crop, script, text_type))
            elif script == ScriptType.GUJARATI:
                batches["gujarati"].append((idx, bbox, crop, script, text_type))
            else:
                batches["latin"].append((idx, bbox, crop, script, text_type))

        return batches
