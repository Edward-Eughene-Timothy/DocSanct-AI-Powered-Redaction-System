
# DocSanct AI-Powered Redaction System — Copilot Instructions

## Architecture Overview
- **Frontend (Django, `frontend/`)**: Handles user uploads via `upload.html`, streams redacted zip files for download. Communicates with backend using Python `requests` (not AJAX).
- **Backend (FastAPI, `backend/redacted_files/back_end.py`)**: `/redact` endpoint receives files, saves to disk, triggers batch redaction, returns zip archive. CORS enabled for cross-port communication.
- **Batch Redaction (`batch/batch_processing.py`)**: Orchestrates multi-file redaction. Calls VLM/AI logic for each file, compresses results. Key entry: `batch_process_files(upload_dir)`.
- **AI Redaction (`ai/pii_detection.py`)**: Vision-Language Model (VLM) for image/PDF redaction. Exposes `redact_image_with_vlm` and `redact_pdf_with_vlm`. Handles metadata removal and encryption.

## Workflow Summary
1. User uploads files (PDF/image) via Django frontend.
2. Frontend POSTs files to FastAPI `/redact` endpoint (port 8001 by default).
3. Backend saves files to `/home/edwardeughenetimothy/Documents/RAW_DATA/REDACT_PDFs` or `/REDACT_PICs`.
4. Batch processor redacts each file using VLM/AI logic, saves redacted output to `backend/redacted_files/`.
5. All redacted files are zipped and streamed back to the user.

## Key Patterns & Conventions
- **File Routing**:
  - Uploads: `/home/edwardeughenetimothy/Documents/RAW_DATA/REDACT_PDFs` (PDFs), `/REDACT_PICs` (images)
  - Redacted output: `backend/redacted_files/`
- **Function Exposure**:
  - Use `redact_image_with_vlm` and `redact_pdf_with_vlm` from `ai/pii_detection.py` for all redaction logic.
- **Batch API**:
  - Use `batch_process_files(upload_dir)` and `compress_to_zip(files, zip_path)` from `batch/batch_processing.py`.
- **Integration**:
  - Frontend (`main.py`) uses Django views to POST files to FastAPI, not JavaScript/AJAX.
  - Backend expects multipart file uploads; returns zip archive.
- **Logging**:
  - Backend and batch modules use print statements for step-by-step tracing (file save, batch start, model inference, zip creation).

## External Dependencies
- **FastAPI** (backend API)
- **Django** (frontend web UI)
- **PyPDF2, pdf2image, Pillow, pytesseract** (AI/PII redaction)
- **Uvicorn** (serving FastAPI)

## Example Usage
- Redact a PDF: `redact_pdf_with_vlm(pdf_path, output_path, password)`
- Batch process: `batch_process_files(upload_dir)` then `compress_to_zip(files, zip_path)`
- Run backend: `uvicorn backend.redacted_files.back_end:app --reload --port 8001`

## Agent Guidance
- Always use exposed functions for redaction, not direct file manipulation.
- Respect file routing conventions for input/output.
- When adding new file types, update batch and AI modules for consistent handling.
- For new endpoints, follow FastAPI patterns in `back_end.py`.
- Use print logging for debugging and tracing workflow steps.

---
If any section is unclear, incomplete, or missing, please provide feedback for improvement.
