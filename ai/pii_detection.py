# ── Standard library ────────────────────────────────────────────
import os          # File‑system helpers (paths, env vars, etc.)
import random      # Lightweight randomness (e.g. sample prompts)
import textwrap    # Nicely format long strings for display
import io          # In‑memory byte streams (e.g. image buffers)
import requests    # Simple HTTP requests for downloading assets
import re          # Regular expression operations
import json        # Functions for working with JSON data (parse, serialize)
import pprint 

# ── Numerical computing ─────────────────────────────────────────
import numpy as np  # Core array maths (fast, vectorised operations)
from PIL import (
    Image,        # Core class for opening, manipulating, and saving images
    ImageDraw,    # Module for drawing on images (shapes, text, etc.)
    ImageFont,    # Module for working with different fonts when drawing text
    ImageColor    # Utility for converting color names/formats to Pillow color values
)

# ── Deep‑learning stack ─────────────────────────────────────────
import torch  # Tensor library + GPU acceleration
from transformers import (
    Qwen2_5_VLForConditionalGeneration,  # Multimodal LLM (image+text)
    AutoProcessor,                       # Paired tokenizer/feature‑extractor
)

# ── Imaging & visualisation ─────────────────────────────────────
import matplotlib.pyplot as plt          # Quick plots in notebooks
import matplotlib.patches as patches     # Bounding‑box overlays, etc.

# ── Project‑specific helpers ────────────────────────────────────
from qwen_vl_utils import process_vision_info  # Post‑process Qwen outputs

# ── Notebook conveniences ──────────────────────────────────────
import IPython.display as ipd             # Inline display (images, audio, HTML)

device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "Qwen/Qwen2.5-VL-3B-Instruct"

model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    model_id,
    torch_dtype="auto",     # automatically uses FP16 on GPU, FP32 on CPU
    device_map="auto"       # dispatches layers to the available device(s)
)
processor = AutoProcessor.from_pretrained(model_id)

print(f"Model loaded on: {model.device}")


def _repair_newlines_inside_strings(txt: str) -> str:
    """
    Replace raw newlines that occur *inside* JSON string literals with a space.
    Very lightweight: it simply looks for a quote, then any run of characters
    that is NOT a quote or backslash, then a newline, then continues…
    """
    pattern = re.compile(r'("([^"\\]|\\.)*)\n([^"]*")')
    while pattern.search(txt):
        txt = pattern.sub(lambda m: m.group(1) + r'\n' + m.group(3), txt)
    return txt

def extract_json(code_block: str, parse: bool = True):
    """
    Remove Markdown code-block markers (``` or ```json) and return:
      • the raw JSON string   (parse=False, default)
      • the parsed Python obj (parse=True)
    """
    # Look for triple-backtick blocks, optionally tagged with a language (e.g. ```json)
    block_re = re.compile(r"```(?:\w+)?\s*(.*?)\s*```", re.DOTALL)
    m = block_re.search(code_block)
    payload = (m.group(1) if m else code_block).strip()
    if parse:
        try:
            return json.loads(payload)
        except json.JSONDecodeError as e:
            # attempt a mild repair and retry once
            payload_fixed = _repair_newlines_inside_strings(payload)
            return json.loads(payload_fixed)
    else:
        return payload
    
def _text_wh(draw, text, font):
    """
    Return (width, height) of *text* under the given *font*, coping with
    Pillow ≥10.0 (textbbox) and older versions (textsize).
    """
    # Check if the draw object has the 'textbbox' method (Pillow >= 8.0)
    if hasattr(draw, "textbbox"): # Pillow ≥8.0, preferred
        # Get the bounding box of the text
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        # Calculate and return the width and height
        return right - left, bottom - top
    # Check if the draw object has the 'textsize' method (Pillow < 10.0)
    elif hasattr(draw, "textsize"): # Pillow <10.0
        # Get the size of the text
        return draw.textsize(text, font=font)
    # Fallback for other or older versions of Pillow
    else: # Fallback
        # Get the bounding box from the font itself
        left, top, right, bottom = font.getbbox(text)
        # Calculate and return the width and height
        return right - left, bottom - top


def draw_bboxes(
    img,
    detections,
    box_color="red",
    box_width=3,
    font_size=32,
    text_color="white",
    text_bg="red",
):
    # Create a drawing object for the image
    draw = ImageDraw.Draw(img)
    try:
        # Try to load a TrueType font
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    except OSError:
        # If TrueType font is not found, load the default font
        font = ImageFont.load_default(font_size)

    # Iterate through each detected object
    for det in detections:
        # Extract bounding box coordinates
        x1, y1, x2, y2 = det["bbox_2d"]
        # Get the label of the detected object, default to empty string if not present
        label = str(det.get("label", ""))

    # Draw a filled black rectangle (redaction box) on the image
    draw.rectangle([x1, y1, x2, y2], fill="black")

    # Return the modified image with bounding boxes and labels
    return img

def display_image(img, title="Image"):
  # Display the image
  plt.figure(figsize=(8, 8))
  plt.imshow(img)
  plt.axis("off")
  plt.title(title)
  plt.show()

## Removed hardcoded image URL and related code. Only uploaded images are processed via API/batch.

def inference(model, msgs):
  # Build the full textual prompt that Qwen-VL expects
  text_prompt = processor.apply_chat_template(
    msgs,
    tokenize=False, 
    add_generation_prompt=True
  )
  # Extract vision-modalities from msgs and convert them to model-ready tensors
  image_inputs, video_inputs = process_vision_info(msgs)

  # ── Pack text + vision into model-ready tensors ──────────────────────────────
  inputs = processor(
      text=[text_prompt],      # 1-element batch containing the chat prompt string
      images=image_inputs,     # list of raw PIL images (pre-processed inside processor)
      videos=video_inputs,     # list of raw video clips (if any)
      padding=True,            # pad sequences so text/vision tokens line up in a batch
      return_tensors="pt",     # return a dict of PyTorch tensors (input_ids, pixel_values, …)
  ).to(model.device)           # move every tensor—text & vision—to the model’s GPU/CPU

  # ── Run inference (no gradients, pure generation) ───────────────────────────
  with torch.no_grad():                     # disable autograd to save memory
      generated_ids = model.generate(       # autoregressive decoding
          **inputs,                         # unpack dict into generate(...)
          max_new_tokens=1000               # cap the response to max_new_tokens
      )
  # Extract the newly generated tokens (skip the prompt length)
  output = processor.batch_decode(
      generated_ids[:, inputs.input_ids.shape[-1]:],
      skip_special_tokens=False
  )[0]
  print(f"RAW output:\n {output} \n")

  # The above output will be in the following format
  # ```json
  #  [
	#    {"bbox_2d": [x, y, w, h], "label": "class name"}
  # ]
  # ```<|im_end|>
  # We will use extract_json utility to extract just the JSON object.
  # [
	#    {"bbox_2d": [x, y, w, h], "label": "class name"}
  # ]
  bounding_boxes = extract_json(output)
  if isinstance(bounding_boxes, dict):
      bounding_boxes = [bounding_boxes]
  print("Parsed bounding_boxes:\n")
  pprint.pprint(bounding_boxes, indent=4)
  return bounding_boxes

## Removed global test code and references to 'img'. Only functions for API/batch use remain.
from pdf2image import convert_from_path
from PyPDF2 import PdfReader, PdfWriter

def redact_pdf_with_vlm(pdf_path, output_path, password="redacted123"):
    # Convert PDF pages to images
    pages = convert_from_path(pdf_path)
    redacted_imgs = []
    for page_img in pages:
        # Run VLM model redaction (replace with your actual logic)
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
                    {"type": "image", "image": page_img},
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
        bounding_boxes = inference(model, msgs)
        img_redacted = draw_bboxes(page_img.copy(), bounding_boxes)
        redacted_imgs.append(img_redacted)
    # Save redacted images as PDF
    temp_pdf_path = output_path + ".temp.pdf"
    redacted_imgs[0].save(temp_pdf_path, save_all=True, append_images=redacted_imgs[1:])
    # Remove metadata and encrypt
    reader = PdfReader(temp_pdf_path)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_metadata({})
    writer.encrypt(password)
    with open(output_path, "wb") as f:
        writer.write(f)
    os.remove(temp_pdf_path)
    print(f"Redacted, encrypted PDF saved to: {output_path}")

def redact_image_with_vlm(img, output_path):
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
    bounding_boxes = inference(model, msgs)
    img_redacted = draw_bboxes(img.copy(), bounding_boxes)
    img_redacted.save(output_path)
    print(f"Redacted image saved to: {output_path}")