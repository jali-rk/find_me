"""
Test FAISS index service.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from app.services.index import FaceIndexService


@pytest.fixture
def temp_index_path():
    """Create a temporary path for index file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.faiss"


@pytest.fixture
def index_service(temp_index_path):
    """Create a FaceIndexService instance."""
    return FaceIndexService(temp_index_path, dimension=512)


def test_index_creation(index_service):
    """Test that index is created with correct dimension."""
    assert index_service.dimension == 512
    assert index_service.size() == 0


def test_add_single_embedding(index_service):
    """Test adding a single embedding."""
    embedding = np.random.rand(512).astype(np.float32)
    # Normalize it
    embedding = embedding / np.linalg.norm(embedding)

    ids = index_service.add(embedding)

    assert len(ids) == 1
    assert ids[0] == 0
    assert index_service.size() == 1


def test_add_multiple_embeddings(index_service):
    """Test adding multiple embeddings."""
    embeddings = np.random.rand(5, 512).astype(np.float32)
    # Normalize each
    for i in range(5):
        embeddings[i] = embeddings[i] / np.linalg.norm(embeddings[i])

    ids = index_service.add(embeddings)

    assert len(ids) == 5
    assert ids == [0, 1, 2, 3, 4]
    assert index_service.size() == 5


def test_search_returns_correct_shape(index_service):
    """Test that search returns arrays of correct shape."""
    # Add some embeddings
    embeddings = np.random.rand(10, 512).astype(np.float32)
    for i in range(10):
        embeddings[i] = embeddings[i] / np.linalg.norm(embeddings[i])
    index_service.add(embeddings)

    # Search
    query = np.random.rand(512).astype(np.float32)
    query = query / np.linalg.norm(query)

    scores, ids = index_service.search(query, k=5)

    assert scores.shape == (1, 5)
    assert ids.shape == (1, 5)


def test_search_ordering(index_service):
    """Test that search results are ordered by score descending."""
    # Add embeddings
    embeddings = np.random.rand(10, 512).astype(np.float32)
    for i in range(10):
        embeddings[i] = embeddings[i] / np.linalg.norm(embeddings[i])
    index_service.add(embeddings)

    # Search with first embedding (should match itself best)
    query = embeddings[0:1]
    scores, ids = index_service.search(query, k=5)

    # Scores should be in descending order
    for i in range(len(scores[0]) - 1):
        assert scores[0][i] >= scores[0][i + 1]

    # First result should be the query itself
    assert ids[0][0] == 0


def test_save_and_load(temp_index_path):
    """Test saving and loading index."""
    # Create and populate index
    index1 = FaceIndexService(temp_index_path, dimension=512)
    embeddings = np.random.rand(5, 512).astype(np.float32)
    for i in range(5):
        embeddings[i] = embeddings[i] / np.linalg.norm(embeddings[i])
    index1.add(embeddings)
    index1.save()

    # Load into new instance
    index2 = FaceIndexService(temp_index_path, dimension=512)

    assert index2.size() == 5

    # Search should work on loaded index
    query = embeddings[0:1]
    scores, ids = index2.search(query, k=3)
    assert len(scores[0]) == 3


def test_search_with_empty_index(index_service):
    """Test searching an empty index."""
    query = np.random.rand(512).astype(np.float32)
    query = query / np.linalg.norm(query)

    scores, ids = index_service.search(query, k=5)

    assert scores.shape == (1, 0)
    assert ids.shape == (1, 0)


def test_add_and_search_roundtrip(index_service):
    """Test complete add and search workflow."""
    # Create test embeddings
    num_embeddings = 20
    embeddings = np.random.rand(num_embeddings, 512).astype(np.float32)
    for i in range(num_embeddings):
        embeddings[i] = embeddings[i] / np.linalg.norm(embeddings[i])

    # Add to index
    ids = index_service.add(embeddings)
    assert len(ids) == num_embeddings

    # Search for each embedding
    for i, embedding in enumerate(embeddings):
        scores, result_ids = index_service.search(embedding, k=1)

        # Should find itself as best match
        assert result_ids[0][0] == i
        # Score should be close to 1.0 (perfect match)
        assert scores[0][0] > 0.99
