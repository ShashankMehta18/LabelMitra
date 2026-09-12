"""
Structured schema for extracted Legal Metrology label declarations.

This is the contract Person 3 (AI+OCR) hands to Person 2 (Backend) and
Person 4 (Rule Engine). Every field is a `FieldResult` so downstream code
can always tell "confidently detected" apart from "unknown/missing" --
we never invent a value when the label is unclear.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class FieldStatus(str, Enum):
    DETECTED = "DETECTED"      # confidently extracted from OCR text
    LOW_CONFIDENCE = "LOW_CONFIDENCE"  # a candidate was found but is uncertain -> route to REVIEW
    UNKNOWN = "UNKNOWN"        # not found on the label / could not be parsed


class Evidence(BaseModel):
    """The OCR phrase (and, when available, its location) backing a field."""

    raw_text: str = Field(..., description="The exact OCR-detected phrase used to derive the field")
    ocr_confidence: Optional[float] = Field(
        None, description="EasyOCR confidence (0-1) for the OCR line this evidence came from"
    )
    bbox: Optional[List[List[float]]] = Field(
        None, description="Quadrilateral [[x,y], ...] bounding box of the OCR line, in image pixel coords"
    )
    page: Optional[int] = Field(None, description="1-indexed page number, for multi-page PDFs")


class FieldResult(BaseModel):
    """One extracted declaration field, with status and supporting evidence."""

    value: Optional[str] = Field(None, description="Normalized extracted value. None if UNKNOWN.")
    status: FieldStatus
    reason: Optional[str] = Field(
        None, description="Why this is UNKNOWN/LOW_CONFIDENCE, e.g. 'no matching pattern found on label'"
    )
    evidence: List[Evidence] = Field(default_factory=list)

    @classmethod
    def unknown(cls, reason: str = "No matching declaration found on the label") -> "FieldResult":
        return cls(value=None, status=FieldStatus.UNKNOWN, reason=reason)

    @classmethod
    def detected(cls, value: str, evidence: List[Evidence], low_confidence: bool = False,
                 reason: Optional[str] = None) -> "FieldResult":
        return cls(
            value=value,
            status=FieldStatus.LOW_CONFIDENCE if low_confidence else FieldStatus.DETECTED,
            reason=reason,
            evidence=evidence,
        )


class ExtractedLabel(BaseModel):
    """
    Structured declaration schema for a single packaged-commodity label.

    Field choices follow the Legal Metrology (Packaged Commodities) Rules, 2011
    mandatory-declaration set: product name, manufacturer/packer/importer,
    net quantity, MRP, date information, and consumer-care details.
    """

    product_name: FieldResult
    manufacturer_packer_importer: FieldResult
    net_quantity: FieldResult
    mrp: FieldResult
    mfg_date: FieldResult
    expiry_or_best_before: FieldResult
    consumer_care: FieldResult

    # Raw OCR text is kept alongside the structured fields so the rule engine
    # or a human reviewer can always fall back to it.
    raw_ocr_text: str = ""


class OCRLine(BaseModel):
    """One line/box returned by the OCR engine, before field extraction."""

    text: str
    confidence: float
    bbox: List[List[float]]
    page: int = 1


class ScanResult(BaseModel):
    """Top-level output of the pipeline -- what Person 2's backend receives."""

    source_file: str
    ocr_lines: List[OCRLine]
    extracted: ExtractedLabel
    warnings: List[str] = Field(default_factory=list)
