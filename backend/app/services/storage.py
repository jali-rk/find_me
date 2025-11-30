"""
Provide path helpers for event_dir, photos_dir, metadata_path, index_path.
Save images with ULID-based names.
Local file storage management.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from fastapi.responses import FileResponse
from PIL import Image

from app.core.config import settings
from app.core.logging import get_logger
from app.utils.ids import generate_photo_id

logger = get_logger(__name__)


class StorageService:
    """Manages local file storage for events and photos."""

    def __init__(self, event_id: str):
        """
        Initialize storage service for a specific event.

        Args:
            event_id: Event identifier
        """
        self.event_id = event_id
        self.event_dir = settings.get_event_dir(event_id)

    @property
    def photos_dir(self) -> Path:
        """Directory for storing original photos."""
        return self.event_dir / "photos"

    @property
    def metadata_path(self) -> Path:
        """Path to metadata JSONL file."""
        return self.event_dir / "metadata.jsonl"

    @property
    def index_path(self) -> Path:
        """Path to FAISS index file."""
        return self.event_dir / "index.faiss"

    def ensure_directories(self) -> None:
        """Create event directory structure if it doesn't exist."""
        self.event_dir.mkdir(parents=True, exist_ok=True)
        self.photos_dir.mkdir(exist_ok=True)
        logger.info(f"Ensured directories for event {self.event_id}")

    def save_image(
        self, image: Image.Image, photo_id: Optional[str] = None, ext: str = "jpg"
    ) -> tuple[str, Path]:
        """
        Save an image to the photos directory.

        Args:
            image: PIL Image to save
            photo_id: Optional photo identifier (generates new if None)
            ext: File extension (default: jpg)

        Returns:
            Tuple of (photo_id, absolute_path)
        """
        if photo_id is None:
            photo_id = generate_photo_id()

        filename = f"{photo_id}.{ext}"
        filepath = self.photos_dir / filename
        image.save(filepath, quality=95)
        logger.debug(f"Saved image {photo_id} to {filepath}")

        return photo_id, filepath

    def get_photo_path(self, photo_id: str, ext: str = "jpg") -> Path:
        """
        Get the absolute path for a photo.

        Args:
            photo_id: Photo identifier
            ext: File extension

        Returns:
            Absolute path to the photo file
        """
        return self.photos_dir / f"{photo_id}.{ext}"

    def get_relative_path(self, photo_id: str, ext: str = "jpg") -> str:
        """
        Get the relative path for a photo (for API responses).

        Args:
            photo_id: Photo identifier
            ext: File extension

        Returns:
            Relative path string (e.g., "photos/abc.jpg")
        """
        return f"photos/{photo_id}.{ext}"

    def append_metadata(self, record: dict[str, Any]) -> None:
        """
        Append a metadata record to the JSONL file.

        Args:
            record: Dictionary to append as JSON line
        """
        with open(self.metadata_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def load_metadata(self) -> list[dict[str, Any]]:
        """
        Load all metadata records from JSONL file.

        Returns:
            List of metadata dictionaries
        """
        if not self.metadata_path.exists():
            return []

        records = []
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records

    def photo_exists(self, photo_id: str, ext: str = "jpg") -> bool:
        """Check if a photo file exists."""
        return self.get_photo_path(photo_id, ext).exists()

    def serve_photo(self, photo_id: str, ext: str = "jpg") -> FileResponse:
        """
        Create a FileResponse for serving a photo.

        Args:
            photo_id: Photo identifier
            ext: File extension

        Returns:
            FileResponse for the photo

        Raises:
            FileNotFoundError: If photo doesn't exist
        """
        filepath = self.get_photo_path(photo_id, ext)
        if not filepath.exists():
            raise FileNotFoundError(f"Photo {photo_id} not found")

        media_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
        return FileResponse(filepath, media_type=media_type)

    @staticmethod
    def event_exists(event_id: str) -> bool:
        """
        Check if an event directory exists.

        Args:
            event_id: Event identifier

        Returns:
            True if event directory exists
        """
        return settings.get_event_dir(event_id).exists()

    @staticmethod
    def create_event(event_id: str) -> "StorageService":
        """
        Create a new event and return its StorageService.

        Args:
            event_id: Event identifier

        Returns:
            StorageService instance for the event
        """
        storage = StorageService(event_id)
        storage.ensure_directories()
        return storage
