from uuid import uuid4

from app.services.ocr_service import extract_text
from app.services.rule_service import validate_declarations
from app.services.store import save_scan


def run_pipeline(
    filename: str,
    content_type: str,
    file_bytes: bytes,
) -> dict:

    scan_id = str(uuid4())

    # Step 1: Run the real OCR + extraction module.
    scan_result = extract_text(
        file_bytes=file_bytes,
        content_type=content_type,
    )

    # Step 2: Convert the OCR team's structured fields
    # into the backend's Declaration format.
    declarations = []

    extracted = scan_result.extracted

    fields = {
        "product_name": extracted.product_name,
        "manufacturer_packer_importer": extracted.manufacturer_packer_importer,
        "net_quantity": extracted.net_quantity,
        "mrp": extracted.mrp,
        "mfg_date": extracted.mfg_date,
        "expiry_or_best_before": extracted.expiry_or_best_before,
        "consumer_care": extracted.consumer_care,
    }

    for field_name, field_result in fields.items():
        confidence = None

        if field_result.evidence:
            confidence = max(
                (
                    evidence.ocr_confidence
                    for evidence in field_result.evidence
                    if evidence.ocr_confidence is not None
                ),
                default=None,
            )

        declarations.append({
            "field": field_name,
            "value": field_result.value,
            "confidence": confidence,
        })

    # Step 3: Legal rule validation.
    compliance = validate_declarations(declarations)

    result = {
        "scan_id": scan_id,
        "filename": filename,
        **compliance,
    }

    save_scan(scan_id, result)

    return result
