import cv2
import io
from PIL import Image
import requests
import matplotlib.pyplot as plt
import pytesseract
from pdf2image import convert_from_path
import os
import re
from PyPDF2 import PdfReader, PdfWriter

# OCR for a single image (returns text and bounding boxes)
def ocr_image(image_path):
    img = Image.open(image_path)
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    results = []
    for i in range(len(data['text'])):
        text = data['text'][i]
        if text.strip():
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            results.append({
                'text': text,
                'bbox': [x, y, x + w, y + h]
            })
    return results

# OCR for a PDF (returns list of results per page)
def ocr_pdf(pdf_path):
    pages = convert_from_path(pdf_path)
    all_results = []
    for page_num, page_img in enumerate(pages):
        data = pytesseract.image_to_data(page_img, output_type=pytesseract.Output.DICT)
        page_results = []
        for i in range(len(data['text'])):
            text = data['text'][i]
            if text.strip():
                x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                page_results.append({
                    'text': text,
                    'bbox': [x, y, x + w, y + h]
                })
        all_results.append(page_results)
    return all_results

PDF_DIR = "/home/edwardeughenetimothy/Documents/RAW_DATA/REDACT_PDFs"
IMG_DIR = "/home/edwardeughenetimothy/Documents/RAW_DATA/REDACT_PICs"
REDACTED_DIR = "/home/edwardeughenetimothy/DocSanct-AI-Powered-Redaction-System/backend/redacted_files"

# Supported image extensions
IMG_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

os.makedirs(REDACTED_DIR, exist_ok=True)

# Dummy redaction function (replace with your actual logic)
def redact_image(img, bboxes):
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    for bbox in bboxes:
        draw.rectangle(bbox, fill="black")
    return img

# PII patterns (expand as needed)
PII_PATTERNS = [
    r"account\s*number", r"acc\s*no", r"bank", r"ifsc", r"signature", r"address", r"name", r"email", r"phone", r"contact", r"code", r"pan", r"aadhaar", r"ssn", r"dob", r"date of birth"
]

# Filter OCR results for PII
def filter_pii(results):
    filtered = []
    for item in results:
        text = item['text'].lower()
        if any(re.search(pattern, text) for pattern in PII_PATTERNS):
            filtered.append(item)
    return filtered

# Remove metadata from image
def remove_image_metadata(img):
    data = list(img.getdata())
    img_no_meta = Image.new(img.mode, img.size)
    img_no_meta.putdata(data)
    return img_no_meta

# Remove metadata from PDF and encrypt
def remove_metadata_and_encrypt_pdf(pdf_path, out_path, password):
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    # Remove metadata
    writer.add_metadata({})
    # Encrypt
    writer.encrypt(password)
    with open(out_path, "wb") as f:
        writer.write(f)
    print(f"Saved encrypted PDF: {out_path}")

# Save redacted images
def save_redacted_image(img_path, bboxes):
    img = Image.open(img_path)
    filtered_bboxes = [item['bbox'] for item in filter_pii(bboxes)]
    img_redacted = redact_image(img, filtered_bboxes)
    img_redacted = remove_image_metadata(img_redacted)
    fname = os.path.basename(img_path)
    out_path = os.path.join(REDACTED_DIR, f"redacted_{fname}")
    img_redacted.save(out_path)
    print(f"Saved redacted image: {out_path}")

# Save redacted PDFs
def save_redacted_pdf(pdf_path, all_bboxes, password="redacted123"):
    pages = convert_from_path(pdf_path)
    redacted_imgs = []
    for page_img, bboxes in zip(pages, all_bboxes):
        filtered_bboxes = [item['bbox'] for item in filter_pii(bboxes)]
        img_redacted = redact_image(page_img, filtered_bboxes)
        img_redacted = remove_image_metadata(img_redacted)
        redacted_imgs.append(img_redacted)
    fname = os.path.basename(pdf_path)
    temp_pdf_path = os.path.join(REDACTED_DIR, f"temp_redacted_{os.path.splitext(fname)[0]}.pdf")
    out_path = os.path.join(REDACTED_DIR, f"redacted_{os.path.splitext(fname)[0]}.pdf")
    redacted_imgs[0].save(temp_pdf_path, save_all=True, append_images=redacted_imgs[1:])
    remove_metadata_and_encrypt_pdf(temp_pdf_path, out_path, password)
    os.remove(temp_pdf_path)

# Process all PDFs in the directory
def process_pdfs(pdf_dir):
    for fname in os.listdir(pdf_dir):
        if fname.lower().endswith('.pdf'):
            pdf_path = os.path.join(pdf_dir, fname)
            print(f"Processing PDF: {pdf_path}")
            results = ocr_pdf(pdf_path)
            for page_num, page_results in enumerate(results):
                print(f"  Page {page_num+1} results:")
                for item in page_results:
                    print(f"    Text: {item['text']}, BBox: {item['bbox']}")
            save_redacted_pdf(pdf_path, results)

# Process all images in the directory
def process_images(img_dir):
    for fname in os.listdir(img_dir):
        ext = os.path.splitext(fname)[1].lower()
        if ext in IMG_EXTS:
            img_path = os.path.join(img_dir, fname)
            print(f"Processing Image: {img_path}")
            results = ocr_image(img_path)
            for item in results:
                print(f"  Text: {item['text']}, BBox: {item['bbox']}")
            save_redacted_image(img_path, results)

# Example usage:
if __name__ == "__main__":
    process_pdfs(PDF_DIR)
    process_images(IMG_DIR)