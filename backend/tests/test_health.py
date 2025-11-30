"""
Test health check endpoint.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test that health check returns 200 OK."""
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_check_response_structure():
    """Test that health check response has correct structure."""
    response = client.get("/healthz")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert isinstance(data["status"], str)
