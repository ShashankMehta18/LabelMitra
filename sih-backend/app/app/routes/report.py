from fastapi import APIRouter, HTTPException

from app.services.store import get_scan


router = APIRouter(tags=["Report"])


@router.get("/report/{scan_id}")
def get_report(scan_id: str):

    result = get_scan(scan_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found."
        )

    return result