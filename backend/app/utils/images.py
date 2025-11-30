"""
Open image safely, convert to RGB, optionally resize long side <= 2000px, strip EXIF.
Image processing utilities with safety checks.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Optional, Union

from PIL import Image, ImageOps

from app.core.logging import get_logger

logger = get_logger(__name__)


def safe_open_image(
    source: Union[Path, str, BytesIO], max_size: Optional[int] = 2000
) -> Image.Image:
    """
    Safely open an image file, convert to RGB, resize if needed, and strip EXIF.

    Args:
        source: Path to image file, or BytesIO buffer
        max_size: Maximum dimension (width or height) in pixels. None for no resize.

    Returns:
        PIL Image in RGB mode with EXIF stripped

    Raises:
        IOError: If image cannot be opened or is invalid
    """
    try:
        img = Image.open(source)

        # Convert to RGB (handles RGBA, grayscale, etc.)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if needed (maintain aspect ratio)
        if max_size is not None:
            width, height = img.size
            if width > max_size or height > max_size:
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                logger.debug(f"Resized image from {width}x{height} to {img.size}")

        # Strip EXIF data for privacy
        img_data = BytesIO()
        img.save(img_data, format="JPEG", quality=95)
        img_data.seek(0)
        img = Image.open(img_data)

        return img

    except Exception as e:
        logger.error(f"Failed to open image: {e}")
        raise IOError(f"Invalid or corrupted image: {e}") from e


def resize_if_needed(img: Image.Image, max_dimension: int = 2000) -> Image.Image:
    """
    Resize image if either dimension exceeds max_dimension.

    Args:
        img: PIL Image
        max_dimension: Maximum width or height

    Returns:
        Resized PIL Image (or original if small enough)
    """
    width, height = img.size
    if width <= max_dimension and height <= max_dimension:
        return img

    img_copy = img.copy()
    img_copy.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return img_copy


def strip_exif(img: Image.Image) -> Image.Image:
    """
    Remove EXIF data from image for privacy.

    Args:
        img: PIL Image

    Returns:
        PIL Image without EXIF data
    """
    data = BytesIO()
    img.save(data, format="JPEG", quality=95)
    data.seek(0)
    return Image.open(data)


def image_to_bytes(img: Image.Image, format: str = "JPEG", quality: int = 95) -> bytes:
    """
    Convert PIL Image to bytes.

    Args:
        img: PIL Image
        format: Output format (JPEG, PNG, etc.)
        quality: Quality for lossy formats (1-100)

    Returns:
        Image as bytes
    """
    buffer = BytesIO()
    img.save(buffer, format=format, quality=quality)
    return buffer.getvalue()
