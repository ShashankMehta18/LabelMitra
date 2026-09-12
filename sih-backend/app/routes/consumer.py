import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.vision_service import analyze_consumer_image


router = APIRouter(tags=["Consumer"])

ALLOWED_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/consumer/scan")
async def consumer_scan(file: UploadFile = File(...)):

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type. Use JPG, PNG, or WEBP.",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image is empty.",
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Image is larger than 10 MB.",
        )

    extension = ALLOWED_TYPES[file.content_type]

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        result = analyze_consumer_image(temp_path)

        return {
            "success": True,
            "data": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Consumer AI analysis failed: {exc}",
        ) from exc

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)