"""
API dependencies for dependency injection.
"""

from app.services.face import FaceService, get_face_service


def get_face_service_dep() -> FaceService:
    """Dependency for face service."""
    return get_face_service()
