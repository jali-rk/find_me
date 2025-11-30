"""
Pytest configuration and shared fixtures.
"""

import pytest


@pytest.fixture
def sample_event_id():
    """Sample event ID for testing."""
    return "01HXEXAMPLE123456789"


@pytest.fixture
def sample_photo_id():
    """Sample photo ID for testing."""
    return "01HXPHOTO123456789ABC"
