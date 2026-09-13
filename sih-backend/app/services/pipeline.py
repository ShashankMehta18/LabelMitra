from uuid import uuid4

from app.services.ocr_service import extract_text
from app.services.rule_service import validate_declarations
from app.services.store import save_scan


FIELDS = [
    "product_name",
    "manufacturer_packer_importer",
    "net_quantity",
    "mrp",
    "mfg_date",
    "expiry_or_best_before",
    "consumer_care",
]


def _get_confidence(field_result):
    if not field_result or not field_result.evidence:
        return None

    confidences = [
        evidence.ocr_confidence
        for evidence in field_result.evidence
        if evidence.ocr_confidence is not None
    ]

    return max(confidences, default=None)


def _merge_results(scan_results):
    """
    Merge extraction results from multiple images.

    For each field, choose the non-empty value with
    the highest available OCR confidence.
    """

    merged = {}

    for field in FIELDS:
        candidates = []

        for scan_result in scan_results:
            field_result = getattr(scan_result.extracted, field, None)

            if not field_result:
                continue

            value = field_result.value

            if value in (None, "", "null", "None"):
                continue

            confidence = _get_confidence(field_result)

            candidates.append({
                "value": value,
                "confidence": confidence,
            })

        if not candidates:
            merged[field] = {
                "value": None,
                "confidence": None,
            }
            continue

        candidates.sort(
            key=lambda item: (
                item["confidence"]
                if item["confidence"] is not None
                else 0
            ),
            reverse=True,
        )

        merged[field] = candidates[0]

    return merged


def run_pipeline(files: list[dict]) -> dict:
    scan_id = str(uuid4())

    # Step 1: Run OCR + AI extraction on every uploaded image.
    scan_results = []

    for file in files:
        scan_result = extract_text(
            file_bytes=file["file_bytes"],
            content_type=file["content_type"],
        )

        scan_results.append(scan_result)

    if not scan_results:
        raise ValueError("No files were provided.")

    # Step 2: Merge the extracted information from all images.
    merged = _merge_results(scan_results)

    # Step 3: Convert merged fields into backend declarations.
    declarations = []

    for field_name in FIELDS:
        field_data = merged[field_name]

        declarations.append({
            "field": field_name,
            "value": field_data["value"],
            "confidence": field_data["confidence"],
        })

    # Step 4: Run the legal rule engine once on the merged result.
    compliance = validate_declarations(declarations)

    filenames = [
        file["filename"]
        for file in files
    ]

    result = {
        "scan_id": scan_id,
        "filename": ", ".join(filenames),
        **compliance,
    }

    save_scan(scan_id, result)

    return result