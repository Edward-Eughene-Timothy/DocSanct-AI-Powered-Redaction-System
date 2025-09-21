# Copilot Instructions for DocSanct AI-Powered Redaction System

## Project Architecture
- **Frontend:** Django web UI (`frontend/`), handles user authentication, file upload, and download. Communicates with backend via HTTP.
- **Backend:** FastAPI app (`backend/redacted_files/back_end.py`), exposes `/redact` endpoint for file upload, triggers batch redaction, returns zip archive.
- **AI Redaction:** Vision-Language Model (VLM) logic in `ai/pii_detection.py` and OCR in `ai/redact_by_ocr.py`. Redacts images and PDFs, removes metadata, encrypts output.
- **Batch Processing:** `batch/batch_processing.py` orchestrates multi-file redaction, calls VLM functions, compresses results.

## Key Workflows
- **Redaction Pipeline:**
  1. User uploads files via frontend.
  2. Frontend sends files to FastAPI `/redact` endpoint.
  3. Backend saves files, calls batch processor.
  4. Batch processor invokes VLM/AI logic for each file (PDFs/images).
  5. Redacted files are encrypted and zipped, returned to user.
- **Metadata Removal:** All output files are scrubbed of metadata before saving.
- **PDF Handling:** PDFs are split into images, redacted per page, reassembled, and encrypted.

## Patterns & Conventions
- **File Routing:**
  - Uploads: `/home/edwardeughenetimothy/Documents/RAW_DATA/REDACT_PDFs` and `/REDACT_PICs`
  - Redacted: `/backend/redacted_files/`
- **Function Exposure:**
  - `ai/pii_detection.py` exposes `redact_image_with_vlm` and `redact_pdf_with_vlm` for use by batch/backend.
- **Batch API:**
  - `batch/batch_processing.py` provides `batch_process_files` and `compress_to_zip` for orchestrating redaction and packaging.
- **Frontend/Backend Integration:**
  - Frontend (`main.py`) uses Django views to POST files to FastAPI, streams zip results to user.

## External Dependencies
- **FastAPI** for backend API
- **Django** for frontend web UI
- **PyPDF2, pdf2image, Pillow, pytesseract** for AI/PII redaction
- **Uvicorn** for serving FastAPI

## Examples
- To redact a PDF: `redact_pdf_with_vlm(pdf_path, output_path, password)`
- To batch process: `batch_process_files(upload_dir)` then `compress_to_zip(files, zip_path)`
- To run backend: `uvicorn backend.redacted_files.back_end:app --reload`

## Tips for AI Agents
- Always use exposed functions for redaction, not direct file manipulation.
- Respect file routing conventions for input/output.
- When adding new file types, update batch and AI modules for consistent handling.
- For new endpoints, follow FastAPI patterns in `back_end.py`.

---
If any section is unclear or missing, please request clarification or provide feedback for improvement.
