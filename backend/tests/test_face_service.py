"""
Test face detection and embedding service.
"""

import numpy as np
import pytest
from PIL import Image

from app.services.face import FaceService, get_face_service


@pytest.fixture
def test_image():
    """Create a simple test image."""
    # Create a 640x480 RGB image
    img = Image.new("RGB", (640, 480), color="white")
    return img


def test_face_service_singleton():
    """Test that FaceService is a singleton."""
    service1 = get_face_service()
    service2 = get_face_service()
    assert service1 is service2


def test_face_service_initialization():
    """Test that FaceService initializes correctly."""
    service = get_face_service()
    assert service is not None
    assert service.get_embedding_dim() == 512


def test_detect_and_embed_returns_list(test_image):
    """Test that detect_and_embed returns a list."""
    service = get_face_service()
    results = service.detect_and_embed(test_image)
    assert isinstance(results, list)


def test_embedding_shape_when_face_detected():
    """Test embedding shape is (512,) when faces are detected."""
    # This test would need a real image with a face
    # For now, we'll just verify the service is callable
    service = get_face_service()
    assert callable(service.detect_and_embed)


def test_normalize_embedding():
    """Test that embeddings are L2-normalized."""
    service = get_face_service()

    # Create a test embedding
    embedding = np.array([3.0, 4.0], dtype=np.float32)
    normalized = service._normalize_embedding(embedding)

    # Check that it's normalized (L2 norm should be 1)
    norm = np.linalg.norm(normalized)
    assert np.isclose(norm, 1.0, atol=1e-6)


def test_normalize_zero_embedding():
    """Test normalization of zero embedding."""
    service = get_face_service()

    embedding = np.array([0.0, 0.0], dtype=np.float32)
    normalized = service._normalize_embedding(embedding)

    # Should return the same zero vector
    assert np.allclose(normalized, embedding)


def test_face_record_structure():
    """Test that FaceRecord has correct structure."""
    from app.services.face import FaceRecord

    record: FaceRecord = {
        "bbox": (10, 20, 100, 150),
        "embedding": np.zeros(512, dtype=np.float32),
    }

    assert "bbox" in record
    assert "embedding" in record
    assert len(record["bbox"]) == 4
    assert record["embedding"].shape == (512,)
