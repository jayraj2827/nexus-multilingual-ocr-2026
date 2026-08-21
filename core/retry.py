"""
Fallback A: Crop-Level Targeted Enhancement and Consensus Re-OCR.
Enhances low-confidence text patches using OpenCV filters and re-evaluates.
"""

from typing import Tuple
import numpy as np
from core.types import ExtractedRegion, ScriptType, EngineType, TextType
from core.preprocessor import enhance_crop_for_retry, calculate_image_quality
from core.confidence import compute_multi_signal_confidence, evaluate_routing_decision
from core.recognizers.base import BaseRecognizer
import config


def execute_crop_retry(
    region: ExtractedRegion,
    crop_img: np.ndarray,
    primary_recognizer: BaseRecognizer,
    fallback_vlm_recognizer: BaseRecognizer
) -> ExtractedRegion:
    """
    Executes Fallback A (local image enhancement + re-OCR) and, if still uncertain,
    escalates to Fallback B (VLM client).
    """
    decision = evaluate_routing_decision(region.composite_confidence, region.text_type == TextType.HANDWRITTEN)

    if decision == "ACCEPT":
        return region

    # --- FALLBACK A: OpenCV Enhancement & Re-OCR ---
    if decision == "FALLBACK_A_RETRY":
        enhanced_crop = enhance_crop_for_retry(crop_img)
        retry_res = primary_recognizer.recognize_batch([enhanced_crop])

        if retry_res and retry_res[0]:
            pass2_text, pass2_raw_conf = retry_res[0]
            new_quality = calculate_image_quality(enhanced_crop)
            pass2_composite_conf = compute_multi_signal_confidence(
                raw_ocr_conf=pass2_raw_conf,
                recognized_text=pass2_text,
                script=region.script,
                image_quality=new_quality,
                is_handwritten=(region.text_type == TextType.HANDWRITTEN)
            )

            # Consensus Check: If Pass 1 and Pass 2 text match closely or Pass 2 has higher confidence
            if pass2_composite_conf >= config.CONFIDENCE_ACCEPT_THRESHOLD or pass2_text == region.text:
                return ExtractedRegion(
                    id=region.id,
                    bbox=region.bbox,
                    text=pass2_text if pass2_text else region.text,
                    raw_confidence=max(region.raw_confidence, pass2_raw_conf),
                    composite_confidence=max(region.composite_confidence, pass2_composite_conf),
                    script=region.script,
                    text_type=region.text_type,
                    engine_used=EngineType.FALLBACK_A_RETRY,
                    is_retried=True,
                    retry_pass_count=1
                )

    # --- FALLBACK B: Terminal VLM Escalation (<1.5% of total crops) ---
    vlm_res = fallback_vlm_recognizer.recognize_batch([crop_img])
    if vlm_res and vlm_res[0]:
        vlm_text, vlm_conf = vlm_res[0]
        if vlm_text:
            return ExtractedRegion(
                id=region.id,
                bbox=region.bbox,
                text=vlm_text,
                raw_confidence=vlm_conf,
                composite_confidence=vlm_conf,
                script=region.script,
                text_type=region.text_type,
                engine_used=EngineType.FALLBACK_B_VLM,
                is_retried=True,
                retry_pass_count=2
            )

    return region
