"""
Evaluation metrics and hardware profiling for NexusOCR benchmark suite.
Includes CER (Character Error Rate), WER, Table F1, Latency, and Peak RSS RAM.
"""

import time
import os
import psutil
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass, field


def calculate_cer(reference: str, hypothesis: str) -> float:
    """
    Calculate Character Error Rate (CER).
    CER = (Insertions + Deletions + Substitutions) / Total Reference Characters
    """
    try:
        import jiwer
        if not reference and not hypothesis:
            return 0.0
        if not reference:
            return 1.0
        return float(jiwer.cer(reference, hypothesis))
    except ImportError:
        # Pure Python fallback Levenshtein distance if jiwer is still installing
        return _python_cer(reference, hypothesis)


def calculate_wer(reference: str, hypothesis: str) -> float:
    """
    Calculate Word Error Rate (WER).
    """
    try:
        import jiwer
        if not reference and not hypothesis:
            return 0.0
        if not reference:
            return 1.0
        return float(jiwer.wer(reference, hypothesis))
    except ImportError:
        ref_words = reference.split()
        hyp_words = hypothesis.split()
        if not ref_words:
            return 0.0 if not hyp_words else 1.0
        return _python_cer(" ".join(ref_words), " ".join(hyp_words))


def _python_cer(ref: str, hyp: str) -> float:
    """Lightweight Levenshtein distance for fallback CER."""
    r_len, h_len = len(ref), len(hyp)
    if r_len == 0:
        return 0.0 if h_len == 0 else 1.0

    dp = [[0] * (h_len + 1) for _ in range(r_len + 1)]
    for i in range(r_len + 1):
        dp[i][0] = i
    for j in range(h_len + 1):
        dp[0][j] = j

    for i in range(1, r_len + 1):
        for j in range(1, h_len + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,       # Deletion
                dp[i][j - 1] + 1,       # Insertion
                dp[i - 1][j - 1] + cost  # Substitution
            )
    return dp[r_len][h_len] / r_len


def calculate_table_f1(ref_cells: list, hyp_cells: list) -> float:
    """Compute precision/recall/F1 on extracted table cell contents."""
    if not ref_cells and not hyp_cells:
        return 1.0
    if not ref_cells or not hyp_cells:
        return 0.0

    ref_set = set(str(c).strip().lower() for c in ref_cells if str(c).strip())
    hyp_set = set(str(c).strip().lower() for c in hyp_cells if str(c).strip())

    if not ref_set and not hyp_set:
        return 1.0
    if not ref_set or not hyp_set:
        return 0.0

    intersection = len(ref_set.intersection(hyp_set))
    precision = intersection / len(hyp_set) if hyp_set else 0.0
    recall = intersection / len(ref_set) if ref_set else 0.0

    if precision + recall == 0:
        return 0.0
    return 2.0 * (precision * recall) / (precision + recall)


@dataclass
class ExecutionProfile:
    """Stores benchmark metrics for a single document run."""
    document_name: str
    total_pages: int
    cer: float = 0.0
    wer: float = 0.0
    table_f1: float = 1.0
    latency_ms: float = 0.0
    latency_per_page_ms: float = 0.0
    peak_rss_mb: float = 0.0
    vlm_escalated_count: int = 0
    stage_breakdown: Dict[str, float] = field(default_factory=dict)


class ProfileSession:
    """Context manager to measure runtime latency and peak memory."""
    def __init__(self, document_name: str = "doc", total_pages: int = 1):
        self.doc_name = document_name
        self.pages = max(1, total_pages)
        self.start_time: float = 0.0
        self.start_mem_mb: float = 0.0
        self.process = psutil.Process(os.getpid())
        self.stage_times: Dict[str, float] = {}
        self._current_stage: Optional[str] = None
        self._stage_start: float = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        self.start_mem_mb = self.process.memory_info().rss / (1024 * 1024)
        return self

    def start_stage(self, stage_name: str):
        if self._current_stage:
            self.end_stage()
        self._current_stage = stage_name
        self._stage_start = time.perf_counter()

    def end_stage(self):
        if self._current_stage:
            elapsed = (time.perf_counter() - self._stage_start) * 1000.0
            self.stage_times[self._current_stage] = self.stage_times.get(self._current_stage, 0.0) + elapsed
            self._current_stage = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._current_stage:
            self.end_stage()

    def get_profile(self, reference_text: str = "", hypothesis_text: str = "") -> ExecutionProfile:
        total_time_ms = (time.perf_counter() - self.start_time) * 1000.0
        current_mem_mb = self.process.memory_info().rss / (1024 * 1024)
        peak_mem_mb = max(self.start_mem_mb, current_mem_mb)

        cer = calculate_cer(reference_text, hypothesis_text) if reference_text else 0.0
        wer = calculate_wer(reference_text, hypothesis_text) if reference_text else 0.0

        return ExecutionProfile(
            document_name=self.doc_name,
            total_pages=self.pages,
            cer=cer,
            wer=wer,
            latency_ms=total_time_ms,
            latency_per_page_ms=total_time_ms / self.pages,
            peak_rss_mb=peak_mem_mb,
            stage_breakdown=self.stage_times
        )
