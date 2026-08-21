"""
Unit tests for Multi-Signal Confidence Scoring.
"""

from core.confidence import compute_multi_signal_confidence, evaluate_routing_decision
from core.types import ScriptType


def test_confidence_scoring_clean_text():
    score = compute_multi_signal_confidence(
        raw_ocr_conf=0.95,
        recognized_text="Invoice Number: 90210",
        script=ScriptType.LATIN,
        image_quality=0.90
    )
    assert score >= 0.85
    assert evaluate_routing_decision(score, is_handwritten=False) == "ACCEPT"


def test_confidence_scoring_noisy_text():
    score = compute_multi_signal_confidence(
        raw_ocr_conf=0.40,
        recognized_text="!@#$%||||",
        script=ScriptType.LATIN,
        image_quality=0.30
    )
    assert score < 0.60
    assert evaluate_routing_decision(score, is_handwritten=False) == "FALLBACK_B_VLM"
