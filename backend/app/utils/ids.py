"""
ULID generation for event and photo identifiers.
ULIDs are lexicographically sortable and URL-safe.
"""

from ulid import ULID


def generate_ulid() -> str:
    """
    Generate a new ULID as a string.

    Returns:
        26-character ULID string (URL-safe, sortable)
    """
    return str(ULID())


def generate_event_id() -> str:
    """Generate a unique event identifier."""
    return generate_ulid()


def generate_photo_id() -> str:
    """Generate a unique photo identifier."""
    return generate_ulid()


def generate_face_id() -> str:
    """Generate a unique face identifier."""
    return generate_ulid()
