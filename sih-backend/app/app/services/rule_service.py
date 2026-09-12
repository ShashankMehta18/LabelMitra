def validate_declarations(
    declarations: list[dict],
) -> dict:

    violations = []

    fields = {
        item["field"]
        for item in declarations
    }

    required_fields = {
        "manufacturer",
        "net_quantity",
        "mrp",
        "manufactured",
        "consumer_care",
    }

    for field in required_fields:
        if field not in fields:
            violations.append({
                "field": field,
                "status": "FAIL",
                "reason": f"Required declaration '{field}' was not detected.",
            })

    status = "FAIL" if violations else "PASS"

    return {
        "status": status,
        "declarations": declarations,
        "violations": violations,
        "message": (
            "Compliance checks completed."
            if status == "PASS"
            else "One or more declarations require attention."
        ),
    }