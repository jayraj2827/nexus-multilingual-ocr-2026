"""
NexusOCR FastAPI Application Server.
Serves static frontend (HTML/CSS/JS) and exposes REST API endpoints for document extraction.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
import fitz
import io
from PIL import Image

from pipeline import NexusOCRPipeline
from core.types import DocumentResult
import config

app = FastAPI(title="NexusOCR Engine", version="1.0.0")

# Initialize pipeline instance (CPU-first)
pipeline = NexusOCRPipeline(use_gpu=False)

# Mount static files
frontend_dir = Path(__file__).resolve().parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

UPLOAD_CACHE = config.DATA_DIR / "uploads"
UPLOAD_CACHE.mkdir(parents=True, exist_ok=True)


@app.get("/")
async def serve_index():
    """Serves the main HTML interface."""
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index_path))


@app.post("/api/process", response_model=DocumentResult)
async def process_document_api(
    file: UploadFile = File(...),
    schema_keys: Optional[str] = Form(None)
):
    """
    Receives PDF file upload and executes adaptive multilingual OCR extraction.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = UPLOAD_CACHE / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    keys = [k.strip() for k in schema_keys.split(",")] if schema_keys else None

    try:
        result = pipeline.process_pdf(str(file_path), schema_keys=keys)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")


@app.get("/api/page_image/{filename}/{page_num}")
async def get_page_image(filename: str, page_num: int):
    """
    Renders a single page image as JPEG for bounding-box preview.
    """
    file_path = UPLOAD_CACHE / filename
    if not file_path.exists():
        # Check benchmark suite as fallback
        bench_path = config.BENCHMARK_DIR / filename
        if bench_path.exists():
            file_path = bench_path
        else:
            raise HTTPException(status_code=404, detail="Document file not found.")

    doc = fitz.open(str(file_path))
    if page_num < 1 or page_num > len(doc):
        doc.close()
        raise HTTPException(status_code=400, detail="Invalid page number.")

    page = doc[page_num - 1]
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("jpeg")
    doc.close()

    return Response(content=img_bytes, media_type="image/jpeg")


if __name__ == "__main__":
    import uvicorn
    print("Starting NexusOCR server on http://localhost:8000 ...")
    uvicorn.run("app.py:app", host="127.0.0.1", port=8000, reload=True)
