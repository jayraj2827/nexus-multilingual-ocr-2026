"""
NexusOCR FastAPI Application Server.
Serves the modern web UI and exposes clean REST endpoints for document intelligence.
"""

import sys
import os
import shutil
from pathlib import Path
from typing import Optional

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

# Mount static frontend
frontend_dir = Path(__file__).resolve().parent / "frontend"
app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/")
async def serve_index():
    """Serves the main web UI."""
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index_path))


@app.post("/api/process")
async def process_document_api(
    file: UploadFile = File(...)
):
    """
    Receives PDF document upload and executes 3-pillar extraction.
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
    pix = page.get_pixmap(dpi=config.BASE_RASTER_DPI)
    img_bytes = pix.tobytes("jpeg")
    doc.close()

    return Response(content=img_bytes, media_type="image/jpeg")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    print(f"Starting NexusOCR server on http://127.0.0.1:{port} ...", flush=True)
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=False)
