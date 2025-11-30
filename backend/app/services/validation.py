"""
MIME/extension checks, size checks for uploaded files.
Centralized validation logic for file uploads.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import UploadFile

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Raised when file validation fails."""

    pass


def validate_file_type(filename: str) -> None:
    """
    Validate that the file extension is allowed.

    Args:
        filename: Name of the file

    Raises:
        ValidationError: If file type is not allowed
    """
    ext = Path(filename).suffix.lstrip(".").lower()
    if ext not in settings.allowed_types_set:
        allowed = ", ".join(sorted(settings.allowed_types_set))
        raise ValidationError(
            f"File type '{ext}' not allowed. Allowed types: {allowed}"
        )


def validate_file_size(size: Optional[int]) -> None:
    """
    Validate that the file size is within limits.

    Args:
        size: File size in bytes (None means unknown)

    Raises:
        ValidationError: If file size exceeds limit
    """
    if size is None:
        return  # Cannot validate unknown size

    max_bytes = settings.max_upload_bytes
    if size > max_bytes:
        max_mb = settings.max_upload_mb
        actual_mb = size / (1024 * 1024)
        raise ValidationError(
            f"File size {actual_mb:.1f}MB exceeds limit of {max_mb}MB"
        )


def validate_upload_file(file: UploadFile) -> None:
    """
    Validate an uploaded file for type and size.

    Args:
        file: FastAPI UploadFile

    Raises:
        ValidationError: If validation fails
    """
    if not file.filename:
        raise ValidationError("No filename provided")

    validate_file_type(file.filename)
    validate_file_size(file.size)


def is_valid_image_type(filename: str) -> bool:
    """
    Check if filename has a valid image extension.

    Args:
        filename: Name of the file

    Returns:
        True if valid image type, False otherwise
    """
    ext = Path(filename).suffix.lstrip(".").lower()
    return ext in settings.allowed_types_set
