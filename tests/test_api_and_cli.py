"""
NexusOCR API & CLI Interface Tests.
Verifies all REST endpoints and command line interfaces.
"""

import io
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from app import app
from nexusocr.interfaces.cli.main import main

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
client = TestClient(app)


def test_api_health_endpoint():
    """Verifies GET /api/health returns 200 and schema with hardware detection."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "cuda_available" in data
    assert "gpu_count" in data
    assert "is_amd_hardware" in data
    assert "hardware" in data
    assert "device_type" in data


def test_api_samples_endpoint():
    """Verifies GET /api/samples returns sample documents list."""
    response = client.get("/api/samples")
    assert response.status_code == 200
    samples = response.json()
    assert isinstance(samples, list)
    assert len(samples) > 0


def test_api_process_sample_endpoint():
    """Verifies POST /api/process_sample/{filename} extracts sample."""
    response = client.post("/api/process_sample/test_digital_english.pdf")
    assert response.status_code == 200
    data = response.json()
    assert data["file_name"] == "test_digital_english.pdf"
    assert data["total_pages"] == 1
    assert "NEXUS INVOICE STATEMENT" in data["full_markdown"]


def test_api_process_upload_endpoint():
    """Verifies POST /api/process receives multipart file upload and processes it."""
    pdf_path = FIXTURES_DIR / "test_digital_english.pdf"
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/process",
        files={"file": ("uploaded_test.pdf", file_bytes, "application/pdf")}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_pages"] == 1
    assert len(data["pages"]) == 1


def test_api_page_image_endpoint():
    """Verifies GET /api/page_image/{filename}/{page_num} returns JPEG image."""
    response = client.get("/api/page_image/test_digital_english.pdf/1")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert len(response.content) > 0


def test_cli_health_command():
    """Verifies CLI health subcommand runs without error."""
    code = main(["health"])
    assert code == 0


def test_cli_process_command(capsys):
    """Verifies CLI process subcommand processes document."""
    pdf_path = str(FIXTURES_DIR / "test_digital_english.pdf")
    code = main(["process", pdf_path, "--format", "json"])
    assert code == 0
    captured = capsys.readouterr()
    assert "test_digital_english.pdf" in captured.out
