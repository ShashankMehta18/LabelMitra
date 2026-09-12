from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.compliance import ComplianceResponse
from app.services.pipeline import run_pipeline


router = APIRouter(tags=["Scan"])


ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/scan", response_model=ComplianceResponse)
async def scan(file: UploadFile = File(...)):

    # 1. Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Use JPG, PNG, or PDF."
        )

    # 2. Read file
    file_bytes = await file.read()

    # 3. Validate empty file
    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    # 4. Validate file size
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File is larger than 10 MB."
        )

    # 5. Send file into processing pipeline
    result = run_pipeline(
        filename=file.filename or "unknown",
        content_type=file.content_type,
        file_bytes=file_bytes,
    )

    return result