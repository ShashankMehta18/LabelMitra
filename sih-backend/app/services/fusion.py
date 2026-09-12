from typing import Any, Dict

from nexora_ocr.schema import FieldResult, FieldStatus


FIELDS = [
    "product_name",
    "manufacturer_packer_importer",
    "net_quantity",
    "mrp",
    "mfg_date",
    "expiry_or_best_before",
    "consumer_care",
]


def fuse(extracted: Any, ai_data: Dict[str, Any]):

    for field in FIELDS:

        ai_value = ai_data.get(field)

        # AI ne value nahi di → OCR value keep karo
        if ai_value in (None, "", "null"):
            continue

        old_result = getattr(extracted, field, None)

        # AI value ko FieldResult ke andar rakho
        new_result = FieldResult(
            value=ai_value,
            status=FieldStatus.LOW_CONFIDENCE,
            reason="Extracted by Vision AI",
            evidence=(
                old_result.evidence
                if isinstance(old_result, FieldResult)
                else []
            ),
        )

        if hasattr(extracted, "model_copy"):

            extracted = extracted.model_copy(
                update={field: new_result}
            )

        elif hasattr(extracted, "copy"):

            extracted = extracted.copy(
                update={field: new_result}
            )

    return extracted