"""
NexusOCR Audio Media Processor.
Handles audio file reading, metadata inspection, and chunking via Python standard library wave.
"""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Dict, Optional, Tuple


class AudioProcessor:
    """Reusable technical operations for audio media without heavy dependencies."""

    @staticmethod
    def get_audio_info(file_path: str) -> Dict[str, float]:
        """Inspects WAV audio properties: channels, sample_rate, duration_sec, sample_width."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        try:
            with wave.open(file_path, "rb") as wf:
                channels = wf.getnchannels()
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                sample_width = wf.getsampwidth()
                duration = n_frames / float(sample_rate) if sample_rate > 0 else 0.0

                return {
                    "channels": float(channels),
                    "sample_rate": float(sample_rate),
                    "duration_sec": duration,
                    "sample_width": float(sample_width),
                    "total_frames": float(n_frames),
                }
        except wave.Error as err:
            raise ValueError(f"Failed to read WAV audio file {file_path}: {err}") from err

    @classmethod
    def read_audio_frames(cls, file_path: str, max_seconds: Optional[float] = None) -> Tuple[Dict[str, float], bytes]:
        """Reads audio metadata and raw frame bytes up to max_seconds."""
        info = cls.get_audio_info(file_path)
        with wave.open(file_path, "rb") as wf:
            if max_seconds:
                frames_to_read = int(info["sample_rate"] * max_seconds)
                raw_bytes = wf.readframes(frames_to_read)
            else:
                raw_bytes = wf.readframes(int(info["total_frames"]))
        return info, raw_bytes
