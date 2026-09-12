from pathlib import Path
from tempfile import NamedTemporaryFile

from nexora_ocr.pipeline import scan_label


def extract_text(
    file_bytes: bytes,
    content_type: str,
):
    extension = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "application/pdf": ".pdf",
    }.get(content_type)

    if extension is None:
        raise ValueError(f"Unsupported content type: {content_type}")

    temp_path = None

    try:
        with NamedTemporaryFile(
            suffix=extension,
            delete=False,
        ) as temp_file:
            temp_file.write(file_bytes)
            temp_path = temp_file.name

        return scan_label(temp_path)

    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
