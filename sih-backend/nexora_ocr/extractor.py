"""
Turns raw OCR lines into the structured ExtractedLabel schema.

Deterministic, regex/keyword-based -- no LLM in this step, matching the
team's "nothing hidden in a black box" approach from the Round-1 deck.
This module NEVER decides PASS/FAIL (that's the rule engine's job); it only
answers "what does the label say", and marks a field UNKNOWN rather than
guessing when nothing on the label supports a value.

v2 change: many real labels print the field name on the left and its value
in a separate text box elsewhere on the label (a different "column" or the
row above/below), rather than "keyword: value" on one line. EasyOCR detects
those correctly as separate text regions, but the original v1 extractor only
ever looked for a value inside the SAME line as the keyword, so it missed
every value printed in a separate box. This version adds a spatial fallback:
when the same-line search comes up empty, it searches other OCR lines near
the keyword's position (by pixel distance) for a match against the field's
value pattern specifically -- not just "any text nearby" -- which is what
lets it correctly pick, say, the one date-shaped string out of a cluttered
label instead of grabbing whatever text happens to be closest.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .schema import Evidence, ExtractedLabel, FieldResult, FieldStatus, OCRLine

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _evidence_from_line(line: OCRLine) -> Evidence:
    return Evidence(
        raw_text=line.text,
        ocr_confidence=line.confidence,
        bbox=line.bbox,
        page=line.page,
    )


def _find_lines(lines: List[OCRLine], pattern: str) -> List[Tuple[OCRLine, re.Match]]:
    """Return every OCR line matching `pattern` (case-insensitive), with its match."""
    compiled = re.compile(pattern, re.IGNORECASE)
    hits = []
    for line in lines:
        m = compiled.search(line.text)
        if m:
            hits.append((line, m))
    return hits


def _line_y(line: OCRLine) -> float:
    return line.bbox[0][1]


def _line_x(line: OCRLine) -> float:
    return line.bbox[0][0]


def _nearby_value_match(
    lines: List[OCRLine],
    anchor: OCRLine,
    value_pattern: str,
    y_window: float = 200.0,
) -> Optional[Tuple[OCRLine, re.Match]]:
    """Search OTHER lines near `anchor` (by vertical pixel distance) for
    `value_pattern`, and return the closest match.

    This handles two-column labels: the field name and its value are
    separate OCR text boxes that don't share a line of text, but do sit
    close together on the physical label. Matching against the field's own
    value pattern (a date shape, a quantity+unit shape, etc.) -- rather than
    grabbing whatever text is nearest -- is what keeps this from picking up
    an unrelated number that just happens to be close by.
    """
    compiled = re.compile(value_pattern, re.IGNORECASE)
    candidates = []
    for line in lines:
        if line is anchor or line.page != anchor.page:
            continue
        m = compiled.search(line.text)
        if not m:
            continue
        y_dist = abs(_line_y(line) - _line_y(anchor))
        if y_dist <= y_window:
            candidates.append((y_dist, line, m))

    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    _, line, m = candidates[0]
    return line, m


# OCR commonly mangles certain characters -- normalize the handful that
# matter for numeric/currency fields before pattern matching.
_OCR_CHAR_FIXES = {
    "₹": "Rs", "Rs.": "Rs", "R$": "Rs",  # currency glyph variants
    "l/-": "/-", "О": "0", "о": "0",     # cyrillic look-alikes seen in some fonts
}


def _normalize(text: str) -> str:
    out = text
    for bad, good in _OCR_CHAR_FIXES.items():
        out = out.replace(bad, good)
    return out


# ---------------------------------------------------------------------------
# Per-field extractors
# ---------------------------------------------------------------------------

_MONEY_PATTERN = r"(?:Rs\.?|₹)\s*[.\-]?\s*(\d+(?:[.,]\d{1,2})?)"


def extract_mrp(lines: List[OCRLine]) -> FieldResult:
    # Primary anchor: the literal "MRP" text.
    hits = _find_lines(lines, r"\bM\.?R\.?P\.?\b")
    # Secondary anchor: MRP declarations are almost always followed by
    # "(incl. of all taxes)" -- useful when OCR mangles "MRP" itself (a
    # known failure mode when a Hindi+English model misreads the letters)
    # but still reads the tax phrase correctly.
    secondary_hits = _find_lines(lines, r"\bINCL\.?\s*(?:OF\s*)?ALL\s*TAX")

    for line, _ in hits + secondary_hits:
        text = _normalize(line.text)
        m = re.search(_MONEY_PATTERN, text)
        if m:
            value = f"Rs. {m.group(1)}"
            low_conf = line.confidence < 0.5
            reason = "OCR confidence below threshold" if low_conf else None
            if (line, _) not in hits:
                reason = ("Matched via the 'incl. of all taxes' phrase near the amount, "
                           "not the literal 'MRP' text (which OCR may have misread)")
                low_conf = True
            return FieldResult.detected(value, [_evidence_from_line(line)], low_confidence=low_conf, reason=reason)

    if not hits and not secondary_hits:
        return FieldResult.unknown("No 'MRP' label or tax-inclusive price phrase found on the scanned text")

    anchor = (hits or secondary_hits)[0][0]
    return FieldResult(
        value=None,
        status=FieldStatus.LOW_CONFIDENCE,
        reason="'MRP'-related text found but no parseable amount next to it",
        evidence=[_evidence_from_line(anchor)],
    )


_QTY_PATTERN = r"\b(\d+(?:\.\d+)?)\s*(g|gm|gms|kg|ml|l|litre|liter|litres|pcs|pieces|pack)\b"


def extract_net_quantity(lines: List[OCRLine]) -> FieldResult:
    # Anchor on a "NET QTY/WT" keyword line first -- labels commonly have
    # several unrelated quantity-shaped numbers (nutrition table rows like
    # "6.6 g"), so searching the whole label for the pattern with no anchor
    # produces false positives. ([NI] tolerates a common OCR misread where
    # "N" comes out as "I".)
    kw_hits = _find_lines(lines, r"\b[NI]ET\s*(QTY|WT|QUANTITY|CONTENTS)\b")

    if kw_hits:
        for line, _ in kw_hits:
            m = re.search(_QTY_PATTERN, _normalize(line.text), re.IGNORECASE)
            if m:
                low_conf = line.confidence < 0.5
                return FieldResult.detected(
                    f"{m.group(1)} {m.group(2).lower()}", [_evidence_from_line(line)],
                    low_confidence=low_conf, reason="OCR confidence below threshold" if low_conf else None,
                )
        # Keyword found but value is in a separate box -- search nearby.
        anchor = kw_hits[0][0]
        nearby = _nearby_value_match(lines, anchor, _QTY_PATTERN)
        if nearby:
            line, m = nearby
            return FieldResult.detected(
                f"{m.group(1)} {m.group(2).lower()}", [_evidence_from_line(line)], low_confidence=True,
                reason="Value found near the 'Net Qty' label in a separate text box, not on the same line",
            )
        return FieldResult(
            value=None, status=FieldStatus.LOW_CONFIDENCE,
            reason="'Net Qty' keyword found but no parseable quantity nearby",
            evidence=[_evidence_from_line(anchor)],
        )

    return FieldResult.unknown("No 'Net Qty/Wt' keyword found on the label")


_DATE_PATTERN = r"\b(\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}|\d{1,2}[/.\-]\d{4}|[A-Za-z]{3,9}\s+\d{4})\b"


def extract_dates(lines: List[OCRLine]) -> Tuple[FieldResult, FieldResult]:
    """Returns (mfg_date, expiry_or_best_before)."""
    mfg_hits = _find_lines(lines, r"\b(MFG|MFD|MANUFACTURE(?:D|D ON)?|PKD|PACKED)\b")
    exp_hits = _find_lines(lines, r"\b(EXP(?:IRY)?|USE BY|BEST BEFORE|BB)\b")

    def _pick_date(text: str, prefer: str) -> Optional[str]:
        # A single combined line like "MFD & USE BY: 12/01/26 & 12/07/26"
        # contains two dates -- pick the first for MFG, the last for
        # EXP/Best-Before, which matches the order they're conventionally
        # printed in (earlier date = manufactured, later date = expiry).
        matches = re.findall(_DATE_PATTERN, text)
        if not matches:
            return None
        return matches[0] if prefer == "first" else matches[-1]

    def _resolve(hits, label: str, prefer: str) -> FieldResult:
        if not hits:
            return FieldResult.unknown(f"No '{label}' keyword found on the label")
        for line, _ in hits:
            value = _pick_date(line.text, prefer)
            if value:
                low_conf = line.confidence < 0.5
                return FieldResult.detected(
                    value, [_evidence_from_line(line)], low_confidence=low_conf,
                    reason="OCR confidence below threshold" if low_conf else None,
                )
        # Keyword found but the date is printed in a separate box -- search nearby.
        anchor = hits[0][0]
        nearby = _nearby_value_match(lines, anchor, _DATE_PATTERN)
        if nearby:
            line, _ = nearby
            value = _pick_date(line.text, prefer)
            return FieldResult.detected(
                value, [_evidence_from_line(line)], low_confidence=True,
                reason=f"Value found near the '{label}' label in a separate text box, not on the same line",
            )
        return FieldResult(
            value=None,
            status=FieldStatus.LOW_CONFIDENCE,
            reason=f"'{label}' keyword found but no parseable date next to it or nearby",
            evidence=[_evidence_from_line(anchor)],
        )

    return _resolve(mfg_hits, "MFG/MFD", "first"), _resolve(exp_hits, "EXP/Best Before", "last")


_PHONE_PATTERN = r"\b(\d{10}|1800[\d\-\s]{6,})\b"
_EMAIL_PATTERN = r"[\w.+-]+@[\w-]+\.[\w.-]+"


def extract_consumer_care(lines: List[OCRLine]) -> FieldResult:
    keyword_hits = _find_lines(
        lines, r"\b(CONSUMER CARE|CUSTOMER CARE|FOR (?:ANY )?(?:QUERIES|COMPLAINTS)|HELPLINE)\b"
    )
    combined_pattern = f"(?:{_PHONE_PATTERN})|(?:{_EMAIL_PATTERN})"

    if keyword_hits:
        for line, _ in keyword_hits:
            phone_m = re.search(_PHONE_PATTERN, line.text)
            email_m = re.search(_EMAIL_PATTERN, line.text)
            if phone_m or email_m:
                value = phone_m.group(1) if phone_m else email_m.group(0)
                low_conf = line.confidence < 0.5
                return FieldResult.detected(
                    value, [_evidence_from_line(line)], low_confidence=low_conf,
                    reason="OCR confidence below threshold" if low_conf else None,
                )
        anchor = keyword_hits[0][0]
        nearby = _nearby_value_match(lines, anchor, combined_pattern)
        if nearby:
            line, m = nearby
            value = m.group(0)
            return FieldResult.detected(
                value, [_evidence_from_line(line)], low_confidence=True,
                reason="Value found near the consumer-care label in a separate text box, not on the same line",
            )
        return FieldResult(
            value=None, status=FieldStatus.LOW_CONFIDENCE,
            reason="Consumer-care section found but no phone number or email could be parsed nearby",
            evidence=[_evidence_from_line(anchor)],
        )

    # No keyword at all -- fall back to a bare phone/email scan (weak signal).
    for line in lines:
        phone_m = re.search(_PHONE_PATTERN, line.text)
        email_m = re.search(_EMAIL_PATTERN, line.text)
        if phone_m or email_m:
            value = phone_m.group(1) if phone_m else email_m.group(0)
            return FieldResult.detected(
                value, [_evidence_from_line(line)], low_confidence=True,
                reason="No 'Consumer Care' keyword found; matched a bare phone/email pattern instead",
            )

    return FieldResult.unknown("No consumer-care phone/email/keyword found")


def extract_manufacturer(lines: List[OCRLine]) -> FieldResult:
    hits = _find_lines(lines, r"\b(MANUFACTURED BY|MARKETED BY|PACKED BY|IMPORTED BY|MFR|MKT\.? BY)\b")
    if not hits:
        return FieldResult.unknown("No 'Manufactured/Marketed/Packed by' declaration found")

    line, match = hits[0]
    remainder = line.text[match.end():].strip(" :,-")
    if remainder:
        low_conf = line.confidence < 0.5
        return FieldResult.detected(
            remainder, [_evidence_from_line(line)], low_confidence=low_conf,
            reason="OCR confidence below threshold" if low_conf else None,
        )

    # Keyword found but nothing followed it on the same line -- the name/
    # address is likely printed as a separate text box nearby. An address
    # has no reliable single pattern, so treat the nearest text line to the
    # right within a tight window as a candidate, rather than searching
    # the whole label (too easy to grab an unrelated line by mistake).
    address_like = r"[A-Za-z]{3,}.*[A-Za-z]{3,}"  # at least two word-like chunks
    nearby = _nearby_value_match(lines, line, address_like, y_window=80.0)
    if nearby:
        cand_line, _ = nearby
        return FieldResult.detected(
            cand_line.text, [_evidence_from_line(cand_line)], low_confidence=True,
            reason="Value found near the manufacturer label in a separate text box, not on the same line",
        )

    return FieldResult(
        value=None,
        status=FieldStatus.LOW_CONFIDENCE,
        reason="Keyword found but no name/address text followed it on the same line or nearby",
        evidence=[_evidence_from_line(line)],
    )


def extract_product_name(lines: List[OCRLine]) -> FieldResult:
    """Heuristic: the highest-confidence line among the first few lines that
    isn't itself a declaration keyword line (MRP/date/etc.) is usually the
    product/brand name -- but we mark it LOW_CONFIDENCE rather than DETECTED,
    since this heuristic is much weaker than the keyword-anchored fields above.
    """
    if not lines:
        return FieldResult.unknown("No text detected on the label at all")

    declaration_kw = re.compile(
        r"\b(MRP|MFG|MFD|EXP|BEST BEFORE|NET|CONSUMER CARE|MANUFACTURED|MARKETED|PACKED|IMPORTED)\b",
        re.IGNORECASE,
    )
    top_region = sorted(lines, key=lambda l: (l.page, l.bbox[0][1]))[:6]
    candidates = [l for l in top_region if not declaration_kw.search(l.text) and len(l.text) >= 3]

    if not candidates:
        return FieldResult.unknown("Could not isolate a likely product-name line near the top of the label")

    best = max(candidates, key=lambda l: l.confidence)
    return FieldResult.detected(
        best.text, [_evidence_from_line(best)], low_confidence=True,
        reason="Positional heuristic (top-of-label line) -- confirm manually, not a keyword-anchored field",
    )


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def extract_fields(lines: List[OCRLine]) -> ExtractedLabel:
    """Raw OCR lines -> validated ExtractedLabel. Never raises on missing
    fields -- missing/uncertain declarations come back as UNKNOWN/LOW_CONFIDENCE,
    which is the correct signal for the rule engine to raise REVIEW rather than
    silently pass or fail a scan.
    """
    mfg_date, expiry_date = extract_dates(lines)

    return ExtractedLabel(
        product_name=extract_product_name(lines),
        manufacturer_packer_importer=extract_manufacturer(lines),
        net_quantity=extract_net_quantity(lines),
        mrp=extract_mrp(lines),
        mfg_date=mfg_date,
        expiry_or_best_before=expiry_date,
        consumer_care=extract_consumer_care(lines),
        raw_ocr_text="\n".join(l.text for l in lines),
    )
