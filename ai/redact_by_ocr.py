import cv2
import io
from PIL import Image
import requests
import matplotlib.pyplot as plt
import pytesseract
from pdf2image import convert_from_path
import os

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

# Supported image extensions
IMG_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}

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

# Example usage:
if __name__ == "__main__":
    process_pdfs(PDF_DIR)
    process_images(IMG_DIR)