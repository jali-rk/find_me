"""
Test match API endpoint.
Integration test for the complete workflow.
"""

import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


@pytest.fixture
def temp_data_dir(monkeypatch):
    """Create a temporary data directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr("app.core.config.settings.data_dir", Path(tmpdir))
        yield Path(tmpdir)


def create_test_image(color="white", size=(640, 480)):
    """Create a test image in memory."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_create_event_and_upload_photos(temp_data_dir):
    """Test creating an event and uploading photos."""
    # Create event
    response = client.post("/api/v1/events")
    assert response.status_code == 201
    data = response.json()
    assert "event_id" in data
    assert "data_dir" in data

    event_id = data["event_id"]

    # Upload photos
    files = [
        ("files", ("photo1.jpg", create_test_image(), "image/jpeg")),
        ("files", ("photo2.jpg", create_test_image(), "image/jpeg")),
    ]

    response = client.post(f"/api/v1/events/{event_id}/photos", files=files)

    # Should be 207 multi-status
    assert response.status_code == 207
    data = response.json()

    assert "event_id" in data
    assert "accepted" in data
    assert "rejected" in data
    assert "totals" in data


def test_upload_photos_to_nonexistent_event():
    """Test uploading photos to an event that doesn't exist."""
    files = [("files", ("photo.jpg", create_test_image(), "image/jpeg"))]

    response = client.post("/api/v1/events/nonexistent/photos", files=files)
    assert response.status_code == 404


def test_match_selfie_to_nonexistent_event():
    """Test matching selfie to an event that doesn't exist."""
    selfie = ("selfie", ("selfie.jpg", create_test_image(), "image/jpeg"))

    response = client.post("/api/v1/events/nonexistent/match", files=[selfie])
    assert response.status_code == 404


def test_match_selfie_no_faces(temp_data_dir):
    """Test matching when no faces are detected."""
    # Create event
    response = client.post("/api/v1/events")
    event_id = response.json()["event_id"]

    # Upload selfie (blank image, no faces)
    selfie = ("selfie", ("selfie.jpg", create_test_image(), "image/jpeg"))

    response = client.post(f"/api/v1/events/{event_id}/match", files=[selfie])

    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data
    assert "results" in data
    assert len(data["results"]) == 0  # No faces detected


def test_get_photo_from_event(temp_data_dir):
    """Test retrieving a photo from an event."""
    # Create event
    response = client.post("/api/v1/events")
    event_id = response.json()["event_id"]

    # Upload a photo
    files = [("files", ("photo.jpg", create_test_image(), "image/jpeg"))]
    response = client.post(f"/api/v1/events/{event_id}/photos", files=files)

    # Get photo_id from response
    data = response.json()
    if data["accepted"]:
        photo_id = data["accepted"][0]["photo_id"]

        # Retrieve photo
        response = client.get(f"/api/v1/events/{event_id}/photos/{photo_id}")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"


def test_get_nonexistent_photo():
    """Test retrieving a photo that doesn't exist."""
    # Create event first
    response = client.post("/api/v1/events")
    event_id = response.json()["event_id"]

    response = client.get(f"/api/v1/events/{event_id}/photos/nonexistent")
    assert response.status_code == 404


def test_upload_invalid_file_type(temp_data_dir):
    """Test uploading an unsupported file type."""
    # Create event
    response = client.post("/api/v1/events")
    event_id = response.json()["event_id"]

    # Try to upload a non-image file
    files = [("files", ("document.txt", io.BytesIO(b"not an image"), "text/plain"))]

    response = client.post(f"/api/v1/events/{event_id}/photos", files=files)

    assert response.status_code == 207
    data = response.json()
    assert len(data["rejected"]) > 0


def test_match_response_structure(temp_data_dir):
    """Test that match response has correct structure."""
    # Create event
    response = client.post("/api/v1/events")
    event_id = response.json()["event_id"]

    # Match with blank selfie
    selfie = ("selfie", ("selfie.jpg", create_test_image(), "image/jpeg"))
    response = client.post(f"/api/v1/events/{event_id}/match", files=[selfie])

    assert response.status_code == 200
    data = response.json()

    # Check structure
    assert "event_id" in data
    assert "results" in data
    assert isinstance(data["results"], list)
