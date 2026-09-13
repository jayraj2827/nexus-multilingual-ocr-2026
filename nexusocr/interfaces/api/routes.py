"""
NexusOCR REST API Route Definitions.
Exposes document processing, sample inspection, page image rendering, and health checks.
"""

from __future__ import annotations

import io
import shutil
from pathlib import Path
from typing import List, Optional

import fitz
from PIL import Image
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse, Response

import nexusocr.config as config
from nexusocr.contracts.formats import (
    FormatCategory,
    FormatResolver,
)
from nexusocr.exceptions import UnsupportedFormatError
from nexusocr.features.batch import BatchDocumentService
from nexusocr.features.document_ocr.service import DocumentOCRService

router = APIRouter()

# Default service instance for API routes
ocr_service = DocumentOCRService()
batch_service = BatchDocumentService(ocr_service)


@router.get("/")
async def serve_index():
    """Serves the main web UI."""
    index_path = config.FRONTEND_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(str(index_path))


@router.get("/api/formats")
async def get_supported_formats():
    """Returns technical catalog of all supported document and image formats."""
    supported_exts = FormatResolver.get_supported_extensions()
    capabilities = [
        FormatResolver.resolve_capability(f"sample{ext}").model_dump()
        for ext in supported_exts
    ]
    return JSONResponse(content={
        "supported_extensions": supported_exts,
        "capabilities": capabilities,
        "unsupported_categories": ["audio", "video"],
        "notice": "NexusOCR is an OCR and document intelligence engine. Audio and video files are not supported."
    })


@router.get("/api/samples")
async def list_sample_documents():
    """Returns available demo sample documents for 1-click evaluation."""
    curated_presets = [
        {
            "name": "test_digital_english.pdf",
            "display": "Digital English Report",
            "type": "Digital PDF",
            "tier": "Tier 1 Fast",
        },
        {
            "name": "test_hindi_devanagari.pdf",
            "display": "Hindi & Devanagari Script",
            "type": "Multilingual PDF",
            "tier": "Tier 1 Multilingual",
        },
        {
            "name": "test_tables_financial.pdf",
            "display": "Financial Statement & Grid",
            "type": "Tabular PDF",
            "tier": "Tier 1 Grid",
        },
        {
            "name": "01_multilingual.pdf",
            "display": "Gujarati & English Document",
            "type": "Multilingual PDF",
            "tier": "Tier 1 Dual-Script",
        },
        {
            "name": "Autonomous_Delivery_Robot_System_Design_Report.docx",
            "display": "System Design Architecture",
            "type": "Office Word",
            "tier": "Office Doc",
        },
        {
            "name": "award.png",
            "display": "Certificate Raster Badge",
            "type": "Scanned Image",
            "tier": "Tier 2 Neural",
        },
    ]
    samples = []
    seen = set()
    for item in curated_presets:
        name = item["name"]
        p_up = config.UPLOAD_DIR / name
        p_fix = config.FIXTURES_DIR / name
        if (p_up.exists() or p_fix.exists()) and name not in seen:
            seen.add(name)
            samples.append(item)

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

    # Ensure present in UPLOAD_DIR for preview rendering
    upload_dest = config.UPLOAD_DIR / filename
    if not upload_dest.exists() and target_path != upload_dest:
        try:
            shutil.copyfile(target_path, upload_dest)
            target_path = upload_dest
        except Exception:
            pass

    try:
        FormatResolver.validate_file(str(target_path))
        result = ocr_service.process_document(str(target_path))
        return JSONResponse(content=jsonable_encoder(result))
    except UnsupportedFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sample processing failed: {str(e)}")


@router.post("/api/process")
async def process_document_api(file: UploadFile = File(...)):
    """Receives document or image upload and executes tiered extraction."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename missing in upload.")

    # Format validation and rejection of audio/video
    try:
        FormatResolver.validate_file(file.filename)
    except UnsupportedFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_path = config.UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = ocr_service.process_document(str(file_path))
        return JSONResponse(content=jsonable_encoder(result))
    except UnsupportedFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")


@router.post("/api/batch")
async def process_batch_api(files: List[UploadFile] = File(...)):
    """Receives multiple document uploads and executes isolated batch extraction."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for batch processing.")

    saved_paths: List[str] = []
    for f in files:
        if not f.filename:
            continue
        dest = config.UPLOAD_DIR / f.filename
        with open(dest, "wb") as buf:
            shutil.copyfileobj(f.file, buf)
        saved_paths.append(str(dest))

    batch_result = batch_service.process_batch(saved_paths)
    return JSONResponse(content=jsonable_encoder(batch_result))


@router.get("/api/page_image/{filename}/{page_num}")
async def get_page_image(filename: str, page_num: int):
    """Renders a single page or image as JPEG for bounding-box preview."""
    file_path = config.UPLOAD_DIR / filename
    if not file_path.exists():
        fixture_path = config.FIXTURES_DIR / filename
        if fixture_path.exists():
            file_path = fixture_path
        else:
            raise HTTPException(status_code=404, detail="Document file not found.")

    ext = file_path.suffix.lower()

    # Handle PDF rendering
    if ext == ".pdf":
        try:
            doc = fitz.open(str(file_path))
            if page_num < 1 or page_num > len(doc):
                doc.close()
                raise HTTPException(status_code=400, detail="Invalid page number.")

            page = doc[page_num - 1]
            pix = page.get_pixmap(dpi=config.BASE_RASTER_DPI)
            img_bytes = pix.tobytes("jpeg")
            doc.close()
            return Response(content=img_bytes, media_type="image/jpeg")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to render PDF page: {e}")

    # Handle raster & multi-frame images (TIFF, PNG, JPG, BMP, WebP)
    image_exts = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
    if ext in image_exts:
        try:
            with Image.open(str(file_path)) as pil_img:
                # Seek to requested page if multi-frame (e.g. TIFF)
                target_frame = page_num - 1
                try:
                    pil_img.seek(target_frame)
                except EOFError:
                    raise HTTPException(status_code=400, detail=f"Frame {page_num} out of bounds.")

                rgb_img = pil_img.convert("RGB")
                buf = io.BytesIO()
                rgb_img.save(buf, format="JPEG", quality=85)
                return Response(content=buf.getvalue(), media_type="image/jpeg")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to render image preview: {e}")

    # Handle Word documents (.docx) preview rendering
    if ext == ".docx":
        try:
            import docx
            from PIL import ImageDraw
            doc = docx.Document(str(file_path))
            img = Image.new("RGB", (800, 1100), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            draw.rectangle([(20, 20), (780, 1080)], outline=(210, 210, 210), width=1)
            draw.rectangle([(40, 40), (760, 95)], fill=(27, 73, 148))
            draw.text((55, 52), filename.replace("_", " ")[:40], fill=(255, 255, 255))
            draw.text((55, 74), "MICROSOFT WORD DOCUMENT PREVIEW", fill=(242, 183, 5))

            y = 120
            for p in doc.paragraphs[:28]:
                txt = p.text.strip()
                if not txt:
                    y += 8
                    continue
                if len(txt) > 85:
                    txt = txt[:85] + "..."
                is_head = txt.startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "Reasons", "Selected", "System", "Microkernel"))
                color = (18, 19, 22) if is_head else (70, 75, 85)
                draw.text((50, y), txt, fill=color)
                y += 24 if is_head else 18
                if y > 1020:
                    break

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            return Response(content=buf.getvalue(), media_type="image/jpeg")
        except Exception:
            pass

    # For other formats without direct page rendering
    placeholder = Image.new("RGB", (800, 1100), color=(248, 249, 250))
    buf = io.BytesIO()
    placeholder.save(buf, format="JPEG")
    return Response(content=buf.getvalue(), media_type="image/jpeg")


@router.get("/api/health")
async def health_check():
    """Returns engine telemetry and hardware status."""
    hw = config.detect_hardware()
    return {
        "status": "healthy",
        "hardware": hw["device_name"],
        "device_name": hw["device_name"],
        "device_type": hw["device_type"],
        "is_amd_hardware": hw["is_amd_hardware"],
        "cuda_available": hw["cuda_available"],
        "gpu_count": hw["gpu_count"],
        "gpu_name": hw["device_name"],
    }

