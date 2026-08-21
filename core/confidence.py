"""
Multi-Signal Confidence Calculator for NexusOCR.
Combines raw OCR probability, script consistency, image quality, and dictionary plausibility.
"""

from typing import Tuple
import re
from core.types import ScriptType, TextType
import config


def compute_multi_signal_confidence(
    raw_ocr_conf: float,
    recognized_text: str,
    script: ScriptType,
    image_quality: float,
    is_handwritten: bool = False
) -> float:
    """
    Computes a balanced confidence metric in [0.0, 1.0].
    """
    if not recognized_text.strip():
        return 0.0

    text = recognized_text.strip()
    char_count = len(text)

    # 1. Base OCR confidence (Weight: 0.45)
    score = 0.45 * max(0.0, min(1.0, raw_ocr_conf))

    # 2. Image Quality & Contrast metric (Weight: 0.15)
    score += 0.15 * max(0.0, min(1.0, image_quality))

    # 3. Language & Character Plausibility (Weight: 0.25)
    # Check ratio of alphanumeric characters vs. suspicious isolated symbols
    alphanumeric = sum(1 for c in text if c.isalnum() or c.isspace())
    alpha_ratio = alphanumeric / char_count if char_count > 0 else 0.0

    # Penalize excessive repeating non-alphanumeric punctuation e.g. "|||||", "....."
    has_repetitive_symbols = bool(re.search(r'([^\w\s])\1{3,}', text))
    plausibility = alpha_ratio * (0.5 if has_repetitive_symbols else 1.0)
    score += 0.25 * plausibility

    # 4. Script Consistency (Weight: 0.15)
    if script == ScriptType.DEVANAGARI:
        # Check proportion of Devanagari Unicode codepoints
        dev_chars = sum(1 for c in text if 0x0900 <= ord(c) <= 0x097F or c.isspace() or c.isdigit())
        script_match = dev_chars / char_count if char_count > 0 else 0.0
        score += 0.15 * script_match
    elif script == ScriptType.GUJARATI:
        guj_chars = sum(1 for c in text if 0x0A80 <= ord(c) <= 0x0AFF or c.isspace() or c.isdigit())
        script_match = guj_chars / char_count if char_count > 0 else 0.0
        score += 0.15 * script_match
    else:
        # Latin
        latin_chars = sum(1 for c in text if c.isascii() and (c.isalnum() or c.isspace() or c in ",.-/;:"))
        script_match = latin_chars / char_count if char_count > 0 else 0.0
        score += 0.15 * script_match

    # Slight penalty for handwriting uncertainty
    if is_handwritten:
        score *= 0.90

    return float(max(0.0, min(1.0, score)))


def evaluate_routing_decision(composite_confidence: float, is_handwritten: bool) -> str:
    """
    Returns action decision: 'ACCEPT', 'FALLBACK_A_RETRY', or 'FALLBACK_B_VLM'
    """
    if composite_confidence >= config.CONFIDENCE_ACCEPT_THRESHOLD:
        return "ACCEPT"

    if is_handwritten or composite_confidence < config.CONFIDENCE_RETRY_THRESHOLD:
        return "FALLBACK_B_VLM"

    return "FALLBACK_A_RETRY"
