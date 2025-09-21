import os
import shutil
import zipfile
from ai.pii_detection import redact_pdf_with_vlm, inference, draw_bboxes, model
from PIL import Image

UPLOAD_DIR = "/home/edwardeughenetimothy/Documents/RAW_DATA"
REDACTED_DIR = "/home/edwardeughenetimothy/DocSanct-AI-Powered-Redaction-System/backend/redacted_files"
ZIP_OUTPUT = os.path.join(REDACTED_DIR, "redacted_documents.zip")

IMG_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
PDF_EXT = '.pdf'

os.makedirs(REDACTED_DIR, exist_ok=True)

def process_and_redact_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    fname = os.path.basename(file_path)
    out_path = os.path.join(REDACTED_DIR, f"redacted_{fname}")
    print(f"Processing file: {file_path} (ext: {ext})")
    if ext in IMG_EXTS:
        print(f"Opening image: {file_path}")
        img = Image.open(file_path)
        print("Preparing VLM messages...")
        msgs = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "You are a document redaction detector. The format of your output must be a valid JSON object "
                            "{'bbox_2d': [x1, y1, x2, y2], 'label': 'class'} "
                            "where 'class' is from : 'Names', 'address', 'date', 'signature','registration_number','other_sensitive_info', 'Bank Details', 'email address',"
                            "'phone number','credit card number','social security number','date of birth','address'."
                        )
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": img},
                    {
                        "type": "text",
                        "text": (
                            "Detect and return bounding boxes for every instance of private information in this image. "
                            "This includes all 'Names', 'addresses', 'signatures', 'dates', 'registration numbers', and any other sensitive info.'Bank Details', 'email address',"
                            "'phone number','credit card number','social security number','date of birth','address'."
                            "Do not skip any field. Return a list of all bounding boxes and their labels in valid JSON."
                        )
                    }
                ],
            }
        ]
        print("Running VLM inference...")
        bounding_boxes = inference(model, msgs)
        print("Bounding boxes:", bounding_boxes)
        print("Drawing bboxes and saving redacted image...")
        img_redacted = draw_bboxes(img.copy(), bounding_boxes)
        img_redacted.save(out_path)
    elif ext == PDF_EXT:
        print(f"Redacting PDF: {file_path}")
        redact_pdf_with_vlm(file_path, out_path, password="redacted123")
    else:
        print(f"Unsupported file type: {file_path}")
    print(f"Processed and saved: {out_path}")
    return out_path

def batch_process_files(upload_dir):
    processed_files = []
    for subdir in ["REDACT_PDFs", "REDACT_PICs"]:
        dir_path = os.path.join(upload_dir, subdir)
        for fname in os.listdir(dir_path):
            file_path = os.path.join(dir_path, fname)
            processed = process_and_redact_file(file_path)
            processed_files.append(processed)
    return processed_files

def compress_to_zip(file_list, zip_path):
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file in file_list:
            zipf.write(file, os.path.basename(file))
    print(f"All redacted files compressed to: {zip_path}")

## Removed local test code. Redaction now only runs via FastAPI endpoint and processes uploaded files.
