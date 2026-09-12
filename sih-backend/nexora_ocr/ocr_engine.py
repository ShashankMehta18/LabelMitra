"""
OCR engine: image/PDF -> list of OCRLine (raw text + confidence + bbox).

Uses EasyOCR (the upgrade path called out in the team's Round-1 deck, moving
off the Tesseract prototype) with light OpenCV preprocessing applied only
where it measurably helps OCR quality, per the Day-1 plan.

This module owns NO business logic (no field extraction, no legal decisions)
-- it only turns pixels into text + confidence, so it can be swapped or
improved without touching the rule engine or the extraction schema.
"""

from __future__ import annotations

import os
from typing import List

import cv2
import numpy as np
from pdf2image import convert_from_path

from .schema import OCRLine

# EasyOCR is imported lazily (see _get_reader) because it's an expensive,
# one-time model load (~seconds) that we don't want to pay at import time,
# e.g. when this module is only used for its schema/preprocessing helpers.
_READER = None


def _get_reader(languages: List[str] | None = None):
    """Lazily create (and cache) the EasyOCR reader.

    Defaults to English only. Testing against a real label showed that
    loading English+Hindi together makes EasyOCR's recognition model misread
    plain English digits and letters as Devanagari look-alikes even when the
    label has no Hindi text at all (e.g. "MRP" became "IIRP", "20" became
    "२०") -- a straight accuracy loss on the common case, since most
    packaged-goods labels in this dataset are English-only or English-
    dominant with just a unit/quantity in Devanagari at most. Pass
    languages=["en", "hi"] explicitly (or via the CLI's --lang flag) for
    labels you know contain real Hindi text.
    """
    global _READER
    if _READER is None:
        import easyocr  # heavy import, done lazily on purpose

        langs = languages or ["en"]
        _READER = easyocr.Reader(langs, gpu=False)
    return _READER


SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png"}
SUPPORTED_PDF_EXTS = {".pdf"}


def load_pages(file_path: str) -> List[np.ndarray]:
    """Load a file into a list of BGR numpy image arrays, one per page.

    Images -> a single-element list. PDFs -> one array per page.
    Raises ValueError for unsupported file types instead of guessing.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext in SUPPORTED_IMAGE_EXTS:
        img = cv2.imread(file_path)
        if img is None:
            raise ValueError(f"Could not read image file: {file_path}")
        return [img]

    if ext in SUPPORTED_PDF_EXTS:
        pil_pages = convert_from_path(file_path, dpi=300)
        pages = []
        for pil_img in pil_pages:
            arr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            pages.append(arr)
        return pages

    raise ValueError(
        f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_IMAGE_EXTS | SUPPORTED_PDF_EXTS)}"
    )


def preprocess(image: np.ndarray) -> np.ndarray:
    """Light, targeted preprocessing -- only steps that reliably help OCR.

    - Upscale small images (OCR on label photos does much better above
      ~1000px on the short side).
    - Deskew using the minAreaRect of dark pixels (corrects camera-angle
      rotation, a common failure mode for phone-photographed labels).
    - CLAHE contrast enhancement on the luminance channel (helps glare/
      low-contrast prints without blowing out already-good images).

    Deliberately does NOT do aggressive binarization/thresholding -- that
    tends to destroy thin fonts on textured packaging backgrounds, which
    hurt OCR more than it helped in testing.
    """
    img = image.copy()

    # 1. Upscale if small
    h, w = img.shape[:2]
    short_side = min(h, w)
    if short_side < 1000:
        scale = 1000 / short_side
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    # 2. Deskew
    img = _deskew(img)

    # 3. CLAHE contrast enhancement (on the L channel of LAB)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    img = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)

    return img


def _deskew(img: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.bitwise_not(gray)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    coords = np.column_stack(np.where(thresh > 0))
    if coords.shape[0] < 20:
        # Not enough foreground pixels to estimate an angle reliably --
        # skip rather than risk rotating a mostly-blank/very-light image.
        return img

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Small angles are camera-shake noise, not real skew -- don't "correct" those.
    if abs(angle) < 0.5 or abs(angle) > 15:
        return img

    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def run_ocr(file_path: str, languages: List[str] | None = None) -> List[OCRLine]:
    """End-to-end: load file -> preprocess each page -> OCR -> OCRLine list.

    Returns raw text lines with confidence and bounding boxes. Does not
    interpret, filter, or validate the text in any way -- that's the
    extractor's job.
    """
    reader = _get_reader(languages)
    pages = load_pages(file_path)

    lines: List[OCRLine] = []
    for page_num, page_img in enumerate(pages, start=1):
        processed = preprocess(page_img)
        # detail=1 returns (bbox, text, confidence) tuples
        results = reader.readtext(processed, detail=1, paragraph=False)
        for bbox, text, confidence in results:
            text = text.strip()
            if not text:
                continue
            lines.append(
                OCRLine(
                    text=text,
                    confidence=float(confidence),
                    bbox=[[float(x), float(y)] for x, y in bbox],
                    page=page_num,
                )
            )
    return lines
