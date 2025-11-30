"""
Load InsightFace model once. Implement detect_and_embed(image) returning list of dicts 
with bbox and 512-d embedding. Ensure embeddings are L2-normalized.
Face detection and embedding generation using InsightFace.
"""

from __future__ import annotations

from typing import Optional, TypedDict

import numpy as np
from insightface.app import FaceAnalysis
from PIL import Image

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FaceRecord(TypedDict):
    """Type definition for face detection result."""

    bbox: tuple[int, int, int, int]  # (x, y, w, h)
    embedding: np.ndarray  # L2-normalized 512-d vector


class FaceService:
    """
    Face detection and embedding service using InsightFace.
    Singleton pattern for model loading.
    """

    _instance: Optional["FaceService"] = None
    _model: Optional[FaceAnalysis] = None

    def __new__(cls) -> "FaceService":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize face analysis model (lazy loading)."""
        if self._model is None:
            self._load_model()

    def _load_model(self) -> None:
        """Load InsightFace model."""
        logger.info(f"Loading InsightFace model: {settings.face_model_name}")
        try:
            self._model = FaceAnalysis(
                name=settings.face_model_name,
                allowed_modules=["detection", "recognition"],
                providers=["CPUExecutionProvider"],
            )
            self._model.prepare(ctx_id=-1, det_size=(640, 640))
            logger.info("InsightFace model loaded successfully")
        except AssertionError as e:
            logger.error(f"Failed to load model {settings.face_model_name}, trying buffalo_l...")
            # Fallback to a more common model
            self._model = FaceAnalysis(
                name="buffalo_l",
                allowed_modules=["detection", "recognition"],
                providers=["CPUExecutionProvider"],
            )
            self._model.prepare(ctx_id=-1, det_size=(640, 640))
            logger.info("InsightFace model loaded successfully with buffalo_l")

    def detect_and_embed(self, image: Image.Image) -> list[FaceRecord]:
        """
        Detect faces in an image and generate embeddings.

        Args:
            image: PIL Image in RGB mode

        Returns:
            List of FaceRecord dicts with bbox and L2-normalized embedding

        Pre-conditions:
            - image must be in RGB mode
            - model must be loaded

        Post-conditions:
            - All embeddings are L2-normalized
            - Bounding boxes are in (x, y, w, h) format relative to original image
        """
        if self._model is None:
            raise RuntimeError("Face model not loaded")

        # Convert PIL Image to numpy array (RGB)
        img_array = np.array(image)

        # Detect faces
        faces = self._model.get(img_array)

        # Convert to our format
        results: list[FaceRecord] = []
        for face in faces:
            # Get bounding box in (x, y, w, h) format
            bbox_xyxy = face.bbox.astype(int)  # [x1, y1, x2, y2]
            x1, y1, x2, y2 = bbox_xyxy
            bbox_xywh = (int(x1), int(y1), int(x2 - x1), int(y2 - y1))

            # Get embedding and normalize
            embedding = face.embedding.astype(np.float32)
            embedding = self._normalize_embedding(embedding)

            results.append(
                FaceRecord(
                    bbox=bbox_xywh,
                    embedding=embedding,
                )
            )

        logger.debug(f"Detected {len(results)} faces in image")
        return results

    @staticmethod
    def _normalize_embedding(embedding: np.ndarray) -> np.ndarray:
        """
        L2-normalize an embedding vector.

        Args:
            embedding: Raw embedding vector

        Returns:
            L2-normalized embedding (unit vector)
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm

    def get_embedding_dim(self) -> int:
        """Get the dimensionality of face embeddings."""
        return settings.embedding_dim


# Global singleton instance
_face_service: Optional[FaceService] = None


def get_face_service() -> FaceService:
    """
    Get or create the global FaceService instance.

    Returns:
        FaceService singleton
    """
    global _face_service
    if _face_service is None:
        _face_service = FaceService()
    return _face_service
