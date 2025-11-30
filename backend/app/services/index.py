"""
Wrap FAISS IndexFlatIP. Provide add(), search(), save(), load(), size() with file locking.
FAISS vector index wrapper for per-event face embeddings.
"""

from __future__ import annotations

import fcntl
from pathlib import Path
from typing import Optional

import faiss
import numpy as np

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FaceIndexService:
    """
    FAISS-based vector index for face embeddings.
    One instance per event, using IndexFlatIP for cosine similarity on normalized vectors.
    """

    def __init__(self, index_path: Path, dimension: int = 512):
        """
        Initialize or load FAISS index.

        Args:
            index_path: Path to save/load the .faiss index file
            dimension: Embedding dimension (default: 512)
        """
        self.index_path = index_path
        self.dimension = dimension
        self._index: faiss.IndexFlatIP

        if index_path.exists():
            self._load()
        else:
            self._create_new()

    def _create_new(self) -> None:
        """Create a new FAISS index."""
        self._index = faiss.IndexFlatIP(self.dimension)
        logger.info(f"Created new FAISS index (dim={self.dimension})")

    def _load(self) -> None:
        """Load existing FAISS index from disk with file locking."""
        with self._file_lock():
            self._index = faiss.read_index(str(self.index_path))
            logger.info(
                f"Loaded FAISS index from {self.index_path} "
                f"({self._index.ntotal} vectors)"
            )

    def add(self, embeddings: np.ndarray) -> list[int]:
        """
        Add embeddings to the index.

        Args:
            embeddings: Array of shape (N, dimension) with L2-normalized vectors

        Returns:
            List of FAISS IDs assigned to the embeddings

        Pre-conditions:
            - embeddings must be L2-normalized
            - embeddings.shape[1] must equal self.dimension
        """
        if embeddings.ndim == 1:
            embeddings = embeddings.reshape(1, -1)

        assert embeddings.shape[1] == self.dimension, (
            f"Embedding dimension mismatch: "
            f"expected {self.dimension}, got {embeddings.shape[1]}"
        )

        start_id = self._index.ntotal
        self._index.add(embeddings.astype(np.float32))
        end_id = self._index.ntotal

        ids = list(range(start_id, end_id))
        logger.debug(f"Added {len(ids)} embeddings to index (total: {self._index.ntotal})")
        return ids

    def search(
        self, query: np.ndarray, k: int = 100
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Search for similar embeddings.

        Args:
            query: Query embedding(s) of shape (N, dimension) or (dimension,)
            k: Number of nearest neighbors to return

        Returns:
            Tuple of (scores, ids) arrays of shape (N, k)
            - scores: Inner product similarities (cosine for normalized vectors)
            - ids: FAISS indices of matches

        Pre-conditions:
            - query must be L2-normalized
        """
        if query.ndim == 1:
            query = query.reshape(1, -1)

        assert query.shape[1] == self.dimension

        # Limit k to index size
        k = min(k, self._index.ntotal)
        if k == 0:
            return np.array([[]]), np.array([[]])

        scores, ids = self._index.search(query.astype(np.float32), k)
        logger.debug(f"Searched index with {query.shape[0]} queries, k={k}")
        return scores, ids

    def save(self) -> None:
        """Save index to disk with file locking."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with self._file_lock():
            faiss.write_index(self._index, str(self.index_path))
            logger.info(f"Saved FAISS index to {self.index_path}")

    def size(self) -> int:
        """Get the number of vectors in the index."""
        return self._index.ntotal

    def _file_lock(self):
        """Context manager for file locking during I/O operations."""
        return _FileLock(self.index_path.parent / f".{self.index_path.name}.lock")

    @staticmethod
    def create_for_event(index_path: Path) -> "FaceIndexService":
        """
        Create a new index for an event.

        Args:
            index_path: Path where index will be saved

        Returns:
            FaceIndexService instance
        """
        return FaceIndexService(index_path, dimension=settings.embedding_dim)


class _FileLock:
    """Simple file-based lock for concurrent access protection."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self.lock_file: Optional[int] = None

    def __enter__(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file = open(self.lock_path, "w")
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file:
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            self.lock_file.close()
