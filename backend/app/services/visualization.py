"""
Visualization service for embeddings and similarity analysis.
Provides t-SNE projections, similarity matrices, and statistics.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import numpy as np
from PIL import Image, ImageDraw
from sklearn.manifold import TSNE

from app.core.logging import get_logger
from app.services.storage import StorageService
from app.utils.ids import generate_ulid

logger = get_logger(__name__)


class VisualizationService:
    """Service for generating visualizations of face embeddings and matches."""

    def __init__(self, storage: StorageService):
        """
        Initialize visualization service.

        Args:
            storage: Storage service for the event
        """
        self.storage = storage

    def get_event_stats(self) -> dict[str, Any]:
        """
        Get statistics for an event.

        Returns:
            Dictionary with photo count, face count, embedding dimension
        """
        metadata = self.storage.load_metadata()

        # Count unique photos
        unique_photos = set(record["photo_id"] for record in metadata)

        return {
            "total_photos": len(unique_photos),
            "total_faces": len(metadata),
            "embedding_dimension": 512,
            "faces_per_photo": (
                round(len(metadata) / len(unique_photos), 2) if unique_photos else 0
            ),
        }

    def compute_tsne_projection(
        self, embeddings: np.ndarray, perplexity: int = 30, random_state: int = 42
    ) -> np.ndarray:
        """
        Compute t-SNE projection of embeddings to 2D.

        Args:
            embeddings: Array of shape (N, 512)
            perplexity: t-SNE perplexity parameter (default: 30)
            random_state: Random seed for reproducibility

        Returns:
            Array of shape (N, 2) with 2D coordinates
        """
        n_samples = embeddings.shape[0]

        # Adjust perplexity - must be less than n_samples
        # Rule of thumb: perplexity should be between 5 and 50, and less than n_samples
        perplexity = min(perplexity, max(2, n_samples - 1))
        
        logger.info(f"Computing t-SNE projection for {n_samples} embeddings (perplexity={perplexity})...")

        tsne = TSNE(
            n_components=2,
            perplexity=perplexity,
            random_state=random_state,
            max_iter=1000,  # Updated from n_iter to max_iter
            verbose=0,
        )

        projection = tsne.fit_transform(embeddings)
        logger.info("t-SNE projection complete")

        return projection

    def get_embedding_projection(self) -> list[dict[str, Any]]:
        """
        Get 2D t-SNE projection of all face embeddings with metadata.

        Returns:
            List of dictionaries with face_id, photo_id, x, y coordinates
        """
        metadata = self.storage.load_metadata()

        if not metadata:
            return []

        # Load FAISS index directly using faiss
        import faiss
        
        index_path = self.storage.index_path
        
        if not index_path.exists():
            logger.warning("No index file found")
            return []

        # Read the index file
        index = faiss.read_index(str(index_path))
        
        if index.ntotal == 0:
            logger.warning("No embeddings found in index")
            return []

        # Extract all embeddings from FAISS index
        embeddings = np.zeros((index.ntotal, index.d), dtype=np.float32)
        for i in range(index.ntotal):
            embeddings[i] = index.reconstruct(int(i))

        # Compute t-SNE projection
        projection_2d = self.compute_tsne_projection(embeddings)

        # Combine with metadata
        result = []
        for i, record in enumerate(metadata):
            result.append({
                "face_id": record["face_id"],
                "photo_id": record["photo_id"],
                "x": float(projection_2d[i, 0]),
                "y": float(projection_2d[i, 1]),
                "embedding_id": record.get("embedding_id", i)
            })

        logger.info(f"Generated t-SNE projection for {len(result)} faces")
        return result

    def compute_similarity_matrix(
        self, embeddings: np.ndarray
    ) -> tuple[np.ndarray, list[str]]:
        """
        Compute pairwise similarity matrix for embeddings.

        Args:
            embeddings: Array of shape (N, 512) with L2-normalized vectors

        Returns:
            Tuple of (similarity_matrix, face_ids)
            - similarity_matrix: (N, N) array of cosine similarities
            - face_ids: List of face IDs corresponding to rows/columns
        """
        # Cosine similarity for normalized vectors is just dot product
        similarity_matrix = np.dot(embeddings, embeddings.T)

        return similarity_matrix, []

    def extract_face_crop(
        self, photo_id: str, bbox: tuple[int, int, int, int], padding: int = 20
    ) -> Optional[Image.Image]:
        """
        Extract a face crop from a photo using bounding box.

        Args:
            photo_id: Photo identifier
            bbox: Bounding box (x, y, w, h)
            padding: Pixels to add around bbox

        Returns:
            PIL Image of the cropped face, or None if photo not found
        """
        photo_path = self.storage.get_photo_path(photo_id)

        if not photo_path.exists():
            logger.warning(f"Photo {photo_id} not found")
            return None

        try:
            img = Image.open(photo_path)
            x, y, w, h = bbox

            # Add padding
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(img.width, x + w + padding)
            y2 = min(img.height, y + h + padding)

            # Crop face
            face_crop = img.crop((x1, y1, x2, y2))

            return face_crop

        except Exception as e:
            logger.error(f"Failed to extract face crop from {photo_id}: {e}")
            return None

    def save_face_crops(self) -> list[dict[str, Any]]:
        """
        Extract and save all face crops for an event.

        Returns:
            List of dictionaries with face metadata and crop paths
        """
        metadata = self.storage.load_metadata()
        faces_dir = self.storage.event_dir / "faces"
        faces_dir.mkdir(exist_ok=True)

        face_crops = []

        for record in metadata:
            photo_id = record["photo_id"]
            face_id = record["face_id"]
            bbox = tuple(record["bbox"])

            # Extract face crop
            face_crop = self.extract_face_crop(photo_id, bbox)

            if face_crop:
                # Save crop
                crop_path = faces_dir / f"{face_id}.jpg"
                face_crop.save(crop_path, quality=90)

                face_crops.append(
                    {
                        "face_id": face_id,
                        "photo_id": photo_id,
                        "bbox": record["bbox"],
                        "crop_path": f"faces/{face_id}.jpg",
                    }
                )

        logger.info(f"Saved {len(face_crops)} face crops")
        return face_crops

    @property
    def faces_dir(self) -> Path:
        """Get the faces directory for this event."""
        return self.storage.event_dir / "faces"

    def get_face_crop_path(self, face_id: str) -> Optional[Path]:
        """
        Get the path to a saved face crop.

        Args:
            face_id: Face identifier

        Returns:
            Path to face crop, or None if not found
        """
        crop_path = self.faces_dir / f"{face_id}.jpg"
        return crop_path if crop_path.exists() else None
