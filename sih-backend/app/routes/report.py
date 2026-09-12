from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.services.store import get_scan
from app.services.report_service import generate_compliance_report


router = APIRouter(tags=["Report"])


@router.get("/report/{scan_id}")
def get_report(scan_id: str):

    result = get_scan(scan_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    return result


@router.get("/report/{scan_id}/pdf")
def download_report_pdf(scan_id: str):

    result = get_scan(scan_id)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Inspection not found.",
        )

    try:
        pdf_path = generate_compliance_report(result)

        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=f"nexora-compliance-{scan_id}.pdf",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not generate compliance report: {exc}",
        ) from exc