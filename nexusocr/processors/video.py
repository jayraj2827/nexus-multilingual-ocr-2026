"""
NexusOCR Video Media Processor.
Handles video frame extraction, keyframe sampling, and video metadata via OpenCV.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple

import cv2
import numpy as np


class VideoProcessor:
    """Reusable technical operations for extracting frames from video media."""

    @staticmethod
    def get_video_info(file_path: str) -> Dict[str, float]:
        """Returns video properties: fps, frame_count, duration_sec, width, height."""
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {file_path}")

        try:
            fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            duration = (total_frames / fps) if fps > 0 else 0.0

            return {
                "fps": fps,
                "frame_count": total_frames,
                "duration_sec": duration,
                "width": width,
                "height": height,
            }
        finally:
            cap.release()

    @classmethod
    def sample_keyframes(
        cls,
        file_path: str,
        sample_interval_sec: float = 1.0,
        max_frames: Optional[int] = None
    ) -> List[Tuple[float, np.ndarray]]:
        """
        Samples video frames at specified time intervals.
        Returns list of (timestamp_seconds, rgb_image_array).
        """
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {file_path}")

        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
        frame_step = max(1, int(round(fps * sample_interval_sec)))
        frames: List[Tuple[float, np.ndarray]] = []

        try:
            current_frame_idx = 0
            while True:
                ret, frame_bgr = cap.read()
                if not ret:
                    break

                if current_frame_idx % frame_step == 0:
                    timestamp = current_frame_idx / fps if fps > 0 else 0.0
                    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                    frames.append((timestamp, frame_rgb))

                    if max_frames and len(frames) >= max_frames:
                        break

                current_frame_idx += 1

            return frames
        finally:
            cap.release()
