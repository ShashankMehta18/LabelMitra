from typing import Annotated

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
MAX_FILES = 5


@router.post("/scan", response_model=ComplianceResponse)
async def scan(
    files: Annotated[list[UploadFile], File(description="Upload up to 5 product images")]
):

    if not files:
        raise HTTPException(
            status_code=400,
            detail="At least one image is required."
        )

    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_FILES} images are allowed per scan."
        )

    validated_files = []

    for file in files:

        if file.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type for {file.filename}. "
                    "Use JPG, PNG, or PDF."
                )
            )

        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded file {file.filename} is empty."
            )

        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File {file.filename} is larger than 10 MB."
            )

        validated_files.append({
            "filename": file.filename or "unknown",
            "content_type": file.content_type,
            "file_bytes": file_bytes,
        })

    try:
        result = run_pipeline(
            files=validated_files
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Scan processing failed: {exc}"
        ) from exc

    return result