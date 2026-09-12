SCANS = {}


def save_scan(scan_id: str, result: dict) -> None:
    SCANS[scan_id] = result


def get_scan(scan_id: str) -> dict | None:
    return SCANS.get(scan_id)