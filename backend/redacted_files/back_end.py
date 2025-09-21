from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from batch.batch_processing import batch_process_files, compress_to_zip

app = FastAPI()

UPLOAD_DIR = "/home/edwardeughenetimothy/Documents/RAW_DATA"
REDACTED_DIR = "/home/edwardeughenetimothy/DocSanct-AI-Powered-Redaction-System/backend/redacted_files"
ZIP_OUTPUT = os.path.join(REDACTED_DIR, "redacted_documents.zip")

@app.post("/redact")
def redact_files(documents: list[UploadFile] = File(...)):
    try:
        # Save uploaded files to appropriate directories
        pdf_dir = os.path.join(UPLOAD_DIR, "REDACT_PDFs")
        img_dir = os.path.join(UPLOAD_DIR, "REDACT_PICs")
        os.makedirs(pdf_dir, exist_ok=True)
        os.makedirs(img_dir, exist_ok=True)
        for file in documents:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext == ".pdf":
                out_path = os.path.join(pdf_dir, file.filename)
            else:
                out_path = os.path.join(img_dir, file.filename)
            with open(out_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
        # Run batch processing
        processed_files = batch_process_files(UPLOAD_DIR)
        compress_to_zip(processed_files, ZIP_OUTPUT)
        # Return the zip file
        return FileResponse(ZIP_OUTPUT, media_type="application/zip", filename="redacted.zip")
    except Exception as e:
        import traceback
        print("Redaction error:", e)
        traceback.print_exc()
        return {"error": str(e)}, 500
