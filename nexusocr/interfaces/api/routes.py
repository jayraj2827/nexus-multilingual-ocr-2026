"""
NexusOCR REST API Route Definitions.
Exposes document processing, sample inspection, page image rendering, and health checks.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, Response

import nexusocr.config as config
from nexusocr.features.document_ocr.service import DocumentOCRService

router = APIRouter()

# Default service instance for API routes
ocr_service = DocumentOCRService()


@router.get("/")
async def serve_index():
    """Serves the main web UI."""
    index_path = config.FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index_path))


@router.get("/api/samples")
async def list_sample_documents():
    """Returns available demo sample documents for 1-click evaluation."""
    samples = []
    fixtures_dir = config.FIXTURES_DIR
    if fixtures_dir.exists():
        for f in fixtures_dir.glob("*.pdf"):
            samples.append({
                "name": f.name,
                "display": f.stem.replace("_", " ").title(),
                "type": "fixture",
            })

    demo_aliases = {
        "12th guj med QP Acc.pdf": "Saheb Tuition 12th Accounts (Printed Gujarati)",
        "12th guj med Answersheet Stat.pdf": "12th Board Answersheet (Handwritten Gujarati)",
        "CBSE_Class10_MathBasicQP.pdf": "CBSE Class 10 Math Exam (Math & Tables)",
        "Multilingual Document OCR  Extraction Pipeline.pdf": "Multilingual Hackathon Deck (13 Pages)",
        "MCA Last Year Marksheet.pdf": "University Marksheet (Dense Financial Table)",
    }
    for filename, display_name in demo_aliases.items():
        p = config.UPLOAD_DIR / filename
        if p.exists():
            samples.append({
                "name": filename,
                "display": display_name,
                "type": "demo",
            })

    return JSONResponse(content=samples)


@router.post("/api/process_sample/{filename}")
async def process_sample_document(filename: str):
    """1-Click process a preset sample document."""
    target_path = config.UPLOAD_DIR / filename
    if not target_path.exists():
        fixture_path = config.FIXTURES_DIR / filename
        if fixture_path.exists():
            target_path = fixture_path
        else:
            raise HTTPException(status_code=404, detail=f"Sample file '{filename}' not found.")

    try:
        result = ocr_service.process_pdf(str(target_path))
        return JSONResponse(content=jsonable_encoder(result))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sample processing failed: {str(e)}")


@router.post("/api/process")
async def process_document_api(file: UploadFile = File(...)):
    """Receives PDF document upload and executes tiered extraction."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = config.UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = ocr_service.process_pdf(str(file_path))
        return JSONResponse(content=jsonable_encoder(result))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.get("/api/page_image/{filename}/{page_num}")
async def get_page_image(filename: str, page_num: int):
    """Renders a single page image as JPEG for bounding-box preview."""
    file_path = config.UPLOAD_DIR / filename
    if not file_path.exists():
        fixture_path = config.FIXTURES_DIR / filename
        if fixture_path.exists():
            file_path = fixture_path
        else:
            raise HTTPException(status_code=404, detail="Document file not found.")

    doc = fitz.open(str(file_path))
    if page_num < 1 or page_num > len(doc):
        doc.close()
        raise HTTPException(status_code=400, detail="Invalid page number.")

    page = doc[page_num - 1]
    pix = page.get_pixmap(dpi=config.BASE_RASTER_DPI)
    img_bytes = pix.tobytes("jpeg")
    doc.close()

    return Response(content=img_bytes, media_type="image/jpeg")


@router.get("/api/health")
async def health_check():
    """Returns engine telemetry and GPU status."""
    try:
        import paddle
        cuda_avail = bool(paddle.is_compiled_with_cuda())
        gpu_cnt = paddle.device.cuda.device_count() if cuda_avail else 0
        gpu_name = paddle.device.cuda.get_device_name(0) if (cuda_avail and gpu_cnt > 0) else "CPU Only"
    except Exception:
        cuda_avail = False
        gpu_cnt = 0
        gpu_name = "CPU Only"

    return {
        "status": "healthy",
        "cuda_available": cuda_avail,
        "gpu_count": gpu_cnt,
        "gpu_name": gpu_name,
    }
