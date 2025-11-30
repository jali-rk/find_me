"""
Orchestrate detection, indexing, and metadata append as jsonl lines. Return counts and ids.
Photo ingestion pipeline: save -> detect -> embed -> index -> metadata.
"""

from __future__ import annotations

from io import BytesIO
from typing import Optional, TypedDict

import numpy as np
from PIL import Image

from app.core.logging import get_logger
from app.services.face import FaceService, get_face_service
from app.services.index import FaceIndexService
from app.services.storage import StorageService
from app.utils.ids import generate_face_id, generate_photo_id
from app.utils.images import safe_open_image

logger = get_logger(__name__)


class PhotoIngestionResult(TypedDict):
    """Result of ingesting a single photo."""

    photo_id: str
    face_count: int
    path: str


class PipelineService:
    """
    Orchestrates the photo ingestion pipeline.
    Handles: image processing -> face detection -> embedding -> indexing -> metadata.
    """

    def __init__(
        self,
        storage: StorageService,
        index: FaceIndexService,
        face_service: Optional[FaceService] = None,
    ):
        """
        Initialize pipeline service.

        Args:
            storage: Storage service for the event
            index: FAISS index service for the event
            face_service: Face detection service (uses global if None)
        """
        self.storage = storage
        self.index = index
        self.face_service = face_service or get_face_service()

    def ingest_photo(
        self, image_data: BytesIO, original_filename: str
    ) -> PhotoIngestionResult:
        """
        Ingest a single photo through the complete pipeline.

        Args:
            image_data: Image data as BytesIO
            original_filename: Original filename (for extension detection)

        Returns:
            PhotoIngestionResult with photo_id, face_count, and path

        Raises:
            Exception: If any step fails
        """
        # 1. Load and process image
        image = safe_open_image(image_data, max_size=2000)
        width, height = image.size

        # 2. Generate photo ID and save image
        photo_id = generate_photo_id()
        _, saved_path = self.storage.save_image(image, photo_id=photo_id, ext="jpg")

        # 3. Detect faces and generate embeddings
        faces = self.face_service.detect_and_embed(image)

        if not faces:
            logger.info(f"No faces detected in photo {photo_id}")
            return PhotoIngestionResult(
                photo_id=photo_id,
                face_count=0,
                path=self.storage.get_relative_path(photo_id),
            )

        # 4. Add embeddings to index
        embeddings = np.array([face["embedding"] for face in faces])
        embedding_ids = self.index.add(embeddings)

        # 5. Save metadata for each face
        for face, embedding_id in zip(faces, embedding_ids):
            face_id = generate_face_id()
            x, y, w, h = face["bbox"]

            metadata = {
                "face_id": face_id,
                "photo_id": photo_id,
                "path": self.storage.get_relative_path(photo_id),
                "bbox": [x, y, w, h],
                "embedding_id": embedding_id,
                "width": width,
                "height": height,
            }
            self.storage.append_metadata(metadata)

        # 6. Save index
        self.index.save()

        logger.info(
            f"Ingested photo {photo_id}: {len(faces)} faces, "
            f"index size: {self.index.size()}"
        )

        return PhotoIngestionResult(
            photo_id=photo_id,
            face_count=len(faces),
            path=self.storage.get_relative_path(photo_id),
        )

    def ingest_photos_bulk(
        self, files: list[tuple[BytesIO, str]]
    ) -> tuple[list[PhotoIngestionResult], int]:
        """
        Ingest multiple photos in bulk.

        Args:
            files: List of (image_data, filename) tuples

        Returns:
            Tuple of (results, total_faces)
        """
        results = []
        total_faces = 0

        for image_data, filename in files:
            try:
                result = self.ingest_photo(image_data, filename)
                results.append(result)
                total_faces += result["face_count"]
            except Exception as e:
                logger.error(f"Failed to ingest {filename}: {e}")
                raise

        return results, total_faces
