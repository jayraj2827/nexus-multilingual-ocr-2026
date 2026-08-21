"""
NexusOCR FastAPI Application Server.
Serves the modern web UI and exposes clean REST endpoints for document intelligence.
"""

import sys
import os
import shutil
from pathlib import Path
from typing import Optional, List

# Ensure UTF-8 output encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response, JSONResponse
from fastapi.encoders import jsonable_encoder
import fitz

from pipeline import NexusOCRPipeline
from engine.types import DocumentResult
import config

app = FastAPI(title="NexusOCR Engine", version="2.0.0")

# Initialize pipeline
pipeline = NexusOCRPipeline()

# Paths
BASE_DIR = Path(__file__).resolve().parent
frontend_dir = BASE_DIR / "frontend"
fixtures_dir = BASE_DIR / "tests" / "fixtures"

# Mount static frontend
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/")
async def serve_index():
    """Serves the main web UI."""
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index_path))


@app.get("/api/samples")
async def list_sample_documents():
    """
    Returns available demo sample documents for 1-click hackathon evaluation.
    """
    samples = []
    # Check fixtures directory
    if fixtures_dir.exists():
        for f in fixtures_dir.glob("*.pdf"):
            samples.append({
                "name": f.name,
                "display": f.stem.replace("_", " ").title(),
                "type": "fixture"
            })

    # Check uploads directory for existing rich demo files
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
                "type": "demo"
            })

    return JSONResponse(content=samples)


@app.post("/api/process_sample/{filename}")
async def process_sample_document(filename: str):
    """
    1-Click process a preset sample document.
    """
    target_path = config.UPLOAD_DIR / filename
    if not target_path.exists():
        fixture_path = fixtures_dir / filename
        if fixture_path.exists():
            target_path = fixture_path
        else:
            raise HTTPException(status_code=404, detail=f"Sample file '{filename}' not found.")

    try:
        result = pipeline.process_pdf(str(target_path))
        return JSONResponse(content=jsonable_encoder(result))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sample processing failed: {str(e)}")


@app.post("/api/process")
async def process_document_api(
    file: UploadFile = File(...)
):
    """
    Receives PDF document upload and executes tiered extraction.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = config.UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = pipeline.process_pdf(str(file_path))
        return JSONResponse(content=jsonable_encoder(result))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@app.get("/api/page_image/{filename}/{page_num}")
async def get_page_image(filename: str, page_num: int):
    """
    Renders a single page image as JPEG for bounding-box preview.
    """
    file_path = config.UPLOAD_DIR / filename
    if not file_path.exists():
        fixture_path = fixtures_dir / filename
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


@app.get("/api/health")
async def health_check():
    """Returns engine telemetry and GPU status."""
    import paddle
    return {
        "status": "healthy",
        "cuda_available": paddle.is_compiled_with_cuda(),
        "gpu_count": paddle.device.cuda.device_count() if paddle.is_compiled_with_cuda() else 0,
        "gpu_name": paddle.device.cuda.get_device_name(0) if (paddle.is_compiled_with_cuda() and paddle.device.cuda.device_count() > 0) else "CPU Only"
    }


if __name__ == "__main__":
    import uvicorn
    port = config.SERVER_PORT
    print(f"Starting NexusOCR server on http://127.0.0.1:{port} ...", flush=True)
    uvicorn.run("app:app", host=config.SERVER_HOST, port=port, reload=True)
