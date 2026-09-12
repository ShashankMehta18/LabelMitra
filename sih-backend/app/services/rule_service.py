import re
from typing import Any


REQUIRED_FIELDS = {
    "product_name": "commodity_name",
    "manufacturer_packer_importer": "manufacturer_or_packer_details",
    "net_quantity": "net_quantity",
    "mrp": "mrp",
    "mfg_date": "month_year",
    "consumer_care": "consumer_contact_details",
}


def _is_present(value: Any) -> bool:
    return value not in (None, "", "null", "None")


def _extract_quantity(value: str):
    if not value:
        return None, None

    text = value.lower().strip().replace(",", "")

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*(kg|kgs|g|gm|gms|mg|l|lt|ltr|litre|litres|ml)",
        text,
    )

    if not match:
        return None, None

    quantity = float(match.group(1))
    unit = match.group(2)

    if unit in {"g", "gm", "gms"}:
        return quantity / 1000, "kg"

    if unit == "mg":
        return quantity / 1_000_000, "kg"

    if unit in {"ml"}:
        return quantity / 1000, "litre"

    if unit in {"l", "lt", "ltr", "litre", "litres"}:
        return quantity, "litre"

    return quantity, "kg"


def _extract_mrp(value: str):
    if not value:
        return None

    match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)", value.lower())

    if not match:
        return None

    return float(match.group(1))


def _has_month_year(value: str) -> bool:
    if not value:
        return False

    text = value.lower()

    patterns = [
        r"\b(0?[1-9]|1[0-2])[/.-]\d{2,4}\b",
        r"\b(0?[1-9]|1[0-2])[/.-]\d{2,4}\b",
        r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b",
        r"\b\d{4}[/.-](0?[1-9]|1[0-2])\b",
    ]

    return any(re.search(pattern, text) for pattern in patterns)


def _confidence_status(declarations):
    for item in declarations:
        confidence = item.get("confidence")

        if confidence is not None and confidence < 0.50:
            return True

    return False


def validate_declarations(
    declarations: list[dict],
) -> dict:

    violations = []

    values = {
        item["field"]: item.get("value")
        for item in declarations
    }

    # -------------------------------------------------
    # 1. CONFIDENCE CHECK
    # -------------------------------------------------

    manual_review = _confidence_status(declarations)

    # -------------------------------------------------
    # 2. RULE 6 — REQUIRED DECLARATIONS
    # -------------------------------------------------

    for extracted_field, rule_field in REQUIRED_FIELDS.items():

        value = values.get(extracted_field)

        if not _is_present(value):
            violations.append({
                "rule": "Rule 6",
                "issue": f"Required declaration '{rule_field}' was not detected.",
                "expected": rule_field,
                "detected": None,
                "severity": "HIGH",
                "evidence": "",
            })

    # -------------------------------------------------
    # 3. RULE 12 / 13 — QUANTITY + UNIT
    # -------------------------------------------------

    quantity_value = values.get("net_quantity")

    quantity, unit = _extract_quantity(
        str(quantity_value)
        if _is_present(quantity_value)
        else ""
    )

    if _is_present(quantity_value) and quantity is None:

        violations.append({
            "rule": "Rules 12-13",
            "issue": "Net quantity could not be normalized.",
            "expected": "Valid quantity with SI unit.",
            "detected": quantity_value,
            "severity": "MEDIUM",
            "evidence": "",
        })

    # -------------------------------------------------
    # 4. PROHIBITED QUANTITY WORDS
    # -------------------------------------------------

    if _is_present(quantity_value):

        quantity_text = str(quantity_value).lower()

        prohibited_words = [
            "minimum",
            "not less than",
            "average",
            "about",
            "approximately",
        ]

        for word in prohibited_words:

            if word in quantity_text:

                violations.append({
                    "rule": "Rule 12",
                    "issue": f"Prohibited quantity expression '{word}' detected.",
                    "expected": "Prescribed quantity expression.",
                    "detected": quantity_value,
                    "severity": "HIGH",
                    "evidence": quantity_value,
                })

    # -------------------------------------------------
    # 5. RULE 18 — MRP
    # -------------------------------------------------

    mrp_value = values.get("mrp")

    if _is_present(mrp_value):

        mrp = _extract_mrp(str(mrp_value))

        if mrp is None:

            violations.append({
                "rule": "Rule 18",
                "issue": "MRP could not be interpreted.",
                "expected": "Valid MRP value.",
                "detected": mrp_value,
                "severity": "HIGH",
                "evidence": "",
            })

    # -------------------------------------------------
    # 6. RULE 10 — MANUFACTURER / PACKER DETAILS
    # -------------------------------------------------

    manufacturer_value = values.get(
        "manufacturer_packer_importer"
    )

    if _is_present(manufacturer_value):

        text = str(manufacturer_value).lower()

        if len(text.strip()) < 5:

            violations.append({
                "rule": "Rule 10",
                "issue": "Manufacturer/packer details appear incomplete.",
                "expected": "Complete manufacturer/packer/importer details.",
                "detected": manufacturer_value,
                "severity": "MEDIUM",
                "evidence": manufacturer_value,
            })

    # -------------------------------------------------
    # 7. DATE CHECK
    # -------------------------------------------------

    mfg_date = values.get("mfg_date")

    if _is_present(mfg_date):

        if not _has_month_year(str(mfg_date)):

            violations.append({
                "rule": "Rule 6",
                "issue": "Manufacturing/packing date does not contain a recognizable month/year.",
                "expected": "Month and year declaration.",
                "detected": mfg_date,
                "severity": "MEDIUM",
                "evidence": mfg_date,
            })

    # -------------------------------------------------
    # 8. CONSUMER CARE
    # -------------------------------------------------

    consumer_care = values.get("consumer_care")

    if _is_present(consumer_care):

        text = str(consumer_care)

        if not re.search(r"\d{7,}", text):

            violations.append({
                "rule": "Rule 6",
                "issue": "Consumer-care details may be incomplete.",
                "expected": "Consumer-care contact details.",
                "detected": consumer_care,
                "severity": "LOW",
                "evidence": consumer_care,
            })

    # -------------------------------------------------
    # 9. FINAL STATUS
    # -------------------------------------------------

    if manual_review:
        status = "REVIEW"

    elif violations:
        status = "FAIL"

    else:
        status = "PASS"

    return {
        "status": status,
        "declarations": declarations,
        "violations": violations,
        "message": (
            "Compliance checks completed."
            if status == "PASS"
            else (
                "Manual review required because extraction confidence is low."
                if status == "REVIEW"
                else "One or more Legal Metrology declarations require attention."
            )
        ),
    }