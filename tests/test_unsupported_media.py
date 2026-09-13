"""
NexusOCR Unsupported Media Rejection Tests.
Verifies that all audio and video formats are strictly rejected across FormatResolver,
DocumentOCRService, API routes, and CLI.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from nexusocr.contracts.formats import (
    FormatCategory,
    FormatResolver,
    AUDIO_EXTENSIONS,
    VIDEO_EXTENSIONS,
)
from nexusocr.exceptions import UnsupportedFormatError
from nexusocr.features.document_ocr.service import DocumentOCRService
from nexusocr.interfaces.api.app import app
from nexusocr.interfaces.cli.main import main


AUDIO_SAMPLES = ["speech.mp3", "recording.wav", "track.aac", "audio.flac", "voice.ogg", "song.m4a"]
VIDEO_SAMPLES = ["video.mp4", "movie.avi", "clip.mov", "stream.mkv", "teaser.flv", "web.webm"]


@pytest.mark.parametrize("filename", AUDIO_SAMPLES)
def test_format_resolver_rejects_audio(filename: str):
    """Verifies FormatResolver identifies audio and rejects via validate_file."""
    assert FormatResolver.is_audio(filename) is True
    assert FormatResolver.is_supported(filename) is False

    cap = FormatResolver.resolve_capability(filename)
    assert cap.category == FormatCategory.AUDIO_UNSUPPORTED

    with pytest.raises(UnsupportedFormatError) as exc_info:
        FormatResolver.validate_file(filename)
    assert "Audio file" in str(exc_info.value)
    assert "audio and video processing is not supported" in str(exc_info.value)


@pytest.mark.parametrize("filename", VIDEO_SAMPLES)
def test_format_resolver_rejects_video(filename: str):
    """Verifies FormatResolver identifies video and rejects via validate_file."""
    assert FormatResolver.is_video(filename) is True
    assert FormatResolver.is_supported(filename) is False

    cap = FormatResolver.resolve_capability(filename)
    assert cap.category == FormatCategory.VIDEO_UNSUPPORTED

    with pytest.raises(UnsupportedFormatError) as exc_info:
        FormatResolver.validate_file(filename)
    assert "Video file" in str(exc_info.value)
    assert "audio and video processing is not supported" in str(exc_info.value)


def test_document_service_rejects_audio(tmp_path: Path):
    """Verifies DocumentOCRService raises UnsupportedFormatError when passed audio file."""
    fake_audio = tmp_path / "voice.mp3"
    fake_audio.write_bytes(b"\xff\xfb\x90\x44" + b"\x00" * 100)

    service = DocumentOCRService()
    with pytest.raises(UnsupportedFormatError) as exc_info:
        service.process_document(str(fake_audio))
    assert "Audio file" in str(exc_info.value)


def test_document_service_rejects_video(tmp_path: Path):
    """Verifies DocumentOCRService raises UnsupportedFormatError when passed video file."""
    fake_video = tmp_path / "clip.mp4"
    fake_video.write_bytes(b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 100)

    service = DocumentOCRService()
    with pytest.raises(UnsupportedFormatError) as exc_info:
        service.process_document(str(fake_video))
    assert "Video file" in str(exc_info.value)


def test_api_rejects_audio_upload():
    """Verifies POST /api/process returns HTTP 400 for audio files."""
    client = TestClient(app)
    response = client.post(
        "/api/process",
        files={"file": ("lecture.mp3", b"dummy audio bytes", "audio/mpeg")}
    )
    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "Audio file '.mp3' is not supported" in detail


def test_api_rejects_video_upload():
    """Verifies POST /api/process returns HTTP 400 for video files."""
    client = TestClient(app)
    response = client.post(
        "/api/process",
        files={"file": ("presentation.mp4", b"dummy video bytes", "video/mp4")}
    )
    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "Video file '.mp4' is not supported" in detail


def test_cli_rejects_audio(tmp_path: Path, capsys):
    """Verifies CLI returns exit code 1 when attempting to process audio."""
    fake_audio = tmp_path / "interview.wav"
    fake_audio.write_bytes(b"RIFF" + b"\x00" * 50)

    exit_code = main(["process", str(fake_audio)])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Audio file" in captured.err
