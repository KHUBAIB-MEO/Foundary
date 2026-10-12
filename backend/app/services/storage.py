import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings

# What the first bytes of a real image look like -> (file extension, content type)
ALLOWED_TYPES = {
    "jpg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}

def detect_image_type(data: bytes) -> str | None:
    """Look at the first bytes of the file to find out what it REALLY is.

    We do not trust the file name or the Content-Type sent by the client,
    because the client can lie about both.
    """
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None

async def save_image(file: UploadFile, folder: str = "products") -> tuple[str, str]:
    """Check the image, save it on disk, return (relative_path, content_type)."""
    max_bytes = settings.MAX_IMAGE_SIZE_MB * 1024 * 1024

    # Read one byte more than allowed, so we can tell if the file is too big.
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"Image is too large (max {settings.MAX_IMAGE_SIZE_MB} MB)",
        )
    extension = detect_image_type(data)
    if extension is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Only JPEG, PNG or WEBP images are allowed"
        )

    
    # Our own random name: nobody can overwrite files or guess names.
    new_name = f"{uuid.uuid4().hex}.{extension}"
    folder_path = settings.UPLOAD_DIR / folder
    folder_path.mkdir(parents=True, exist_ok=True)
    (folder_path / new_name).write_bytes(data)

    return f"{folder}/{new_name}", ALLOWED_TYPES[extension]


def delete_file(relative_path: str) -> None:
    """Delete a saved file. Does nothing if it is already gone."""
    path = Path(settings.UPLOAD_DIR) / relative_path
    path.unlink(missing_ok=True)