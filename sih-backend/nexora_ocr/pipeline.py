"""
Nexora OCR + Vision AI Pipeline

IMAGE
  ↓
OCR
  ↓
Vision AI
  ↓
Fusion
  ↓
Structured Result
"""

from __future__ import annotations

from typing import List, Optional

from .extractor import extract_fields
from .ocr_engine import run_ocr
from .schema import ScanResult

from app.services.vision_service import analyze_image
from app.services.fusion import fuse


def scan_label(
    file_path: str,
    languages: Optional[List[str]] = None,
) -> ScanResult:

    warnings: List[str] = []

    # --------------------------------
    # 1. OCR PIPELINE
    # --------------------------------

    try:
        ocr_lines = run_ocr(
            file_path,
            languages=languages,
        )

    except ValueError:
        raise

    if not ocr_lines:
        warnings.append(
            "OCR returned no text at all -- "
            "check image quality/orientation"
        )

    # --------------------------------
    # 2. OCR FIELD EXTRACTION
    # --------------------------------

    extracted = extract_fields(
        ocr_lines
    )

    # --------------------------------
    # 3. VISION AI PIPELINE
    # --------------------------------

    try:
        ai_data = analyze_image(
            file_path
        )

    except Exception as exc:
        raise RuntimeError(
            f"Vision AI failed: {exc}"
        ) from exc

    # --------------------------------
    # 4. OCR + AI FUSION
    # --------------------------------

    if ai_data:
        extracted = fuse(
            extracted,
            ai_data,
        )

    # --------------------------------
    # 5. FINAL STRUCTURED RESULT
    # --------------------------------

    return ScanResult(
        source_file=file_path,
        ocr_lines=ocr_lines,
        extracted=extracted,
        warnings=warnings,
    )