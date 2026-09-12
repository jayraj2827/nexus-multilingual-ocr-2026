"""
NexusOCR Command-Line Interface.
Supports document extraction, system health inspection, and running the server.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

import nexusocr.config as config
from nexusocr.features.document_ocr.service import DocumentOCRService
from nexusocr.logging import log


def build_parser() -> argparse.ArgumentParser:
    """Constructs the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="nexusocr",
        description="NexusOCR: Adaptive Multilingual Document Intelligence Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: process
    proc_parser = subparsers.add_parser("process", help="Process a document through the OCR pipeline")
    proc_parser.add_argument("file", type=str, help="Path to the PDF document to extract")
    proc_parser.add_argument("--max-pages", type=int, default=None, help="Maximum number of pages to process")
    proc_parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    proc_parser.add_argument("--output", "-o", type=str, default=None, help="File to write output to")

    # Command: health
    subparsers.add_parser("health", help="Check OCR and GPU engine availability")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Run the FastAPI web server")
    serve_parser.add_argument("--host", type=str, default=config.SERVER_HOST, help="Server host IP")
    serve_parser.add_argument("--port", type=int, default=config.SERVER_PORT, help="Server port number")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    return parser


def handle_process(args: argparse.Namespace) -> int:
    """Executes document processing via DocumentOCRService."""
    file_path = args.file
    if not Path(file_path).exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    service = DocumentOCRService()
    result = service.process_pdf(file_path, max_pages=args.max_pages)

    if args.format == "json":
        output_content = json.dumps(result.model_dump(), indent=2)
    else:
        output_content = result.full_markdown

    if args.output:
        Path(args.output).write_text(output_content, encoding="utf-8")
        print(f"Output saved to {args.output}")
    else:
        print(output_content)

    return 0


def handle_health(args: argparse.Namespace) -> int:
    """Prints GPU and engine diagnostic information."""
    try:
        import paddle
        cuda_avail = bool(paddle.is_compiled_with_cuda())
        gpu_count = paddle.device.cuda.device_count() if cuda_avail else 0
        gpu_name = paddle.device.cuda.get_device_name(0) if (cuda_avail and gpu_count > 0) else "CPU Only"
    except Exception:
        cuda_avail = False
        gpu_count = 0
        gpu_name = "CPU Only"

    status = {
        "status": "healthy",
        "cuda_available": cuda_avail,
        "gpu_count": gpu_count,
        "gpu_name": gpu_name,
    }
    print(json.dumps(status, indent=2))
    return 0


def handle_serve(args: argparse.Namespace) -> int:
    """Starts the Uvicorn web server."""
    import uvicorn
    print(f"Starting NexusOCR server on http://{args.host}:{args.port} ...", flush=True)
    uvicorn.run("nexusocr.interfaces.api.app:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "process":
        return handle_process(args)
    elif args.command == "health":
        return handle_health(args)
    elif args.command == "serve":
        return handle_serve(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
