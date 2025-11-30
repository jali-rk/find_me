"""
Admin dashboard endpoints for visualization and analytics.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Path as PathParam
from fastapi.responses import FileResponse

from app.core.logging import get_logger
from app.domain.models import ErrorResponse
from app.services.storage import StorageService
from app.services.visualization import VisualizationService
from pydantic import BaseModel, Field

logger = get_logger(__name__)
router = APIRouter(prefix="/admin/events", tags=["admin"])


# Response Models
class EventStatsResponse(BaseModel):
    """Statistics for an event."""

    event_id: str = Field(description="Event identifier")
    total_photos: int = Field(description="Number of unique photos")
    total_faces: int = Field(description="Total faces detected")
    embedding_dimension: int = Field(description="Embedding vector dimension")
    faces_per_photo: float = Field(description="Average faces per photo")


class FaceCropInfo(BaseModel):
    """Information about a face crop."""

    face_id: str = Field(description="Face identifier")
    photo_id: str = Field(description="Source photo identifier")
    bbox: list[int] = Field(description="Bounding box [x, y, w, h]")
    crop_path: str = Field(description="Relative path to face crop")


class FaceCropsResponse(BaseModel):
    """Response with face crop information."""

    event_id: str = Field(description="Event identifier")
    faces: list[FaceCropInfo] = Field(description="List of face crops")


class FaceMetadata(BaseModel):
    """Metadata for a single face."""

    face_id: str = Field(description="Face identifier")
    photo_id: str = Field(description="Photo identifier")
    bbox: list[int] = Field(description="Bounding box [x, y, w, h]")
    embedding_id: int = Field(description="FAISS index ID")


class EventMetadataResponse(BaseModel):
    """All face metadata for an event."""

    event_id: str = Field(description="Event identifier")
    faces: list[FaceMetadata] = Field(description="List of all faces")


class EmbeddingProjection(BaseModel):
    """2D projection of a face embedding."""

    face_id: str = Field(description="Face identifier")
    photo_id: str = Field(description="Photo identifier")
    x: float = Field(description="X coordinate in 2D projection")
    y: float = Field(description="Y coordinate in 2D projection")
    embedding_id: int = Field(description="FAISS index ID")


class ProjectionResponse(BaseModel):
    """t-SNE projection of face embeddings."""

    event_id: str = Field(description="Event identifier")
    projections: list[EmbeddingProjection] = Field(description="2D projections")


@router.get(
    "/{event_id}/stats",
    response_model=EventStatsResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_event_stats(
    event_id: str = PathParam(..., description="Event identifier"),
) -> EventStatsResponse:
    """
    Get statistics for an event.
    Returns counts of photos, faces, and other metrics.
    """
    if not StorageService.event_exists(event_id):
        raise HTTPException(status_code=404, detail="Event not found")

    storage = StorageService(event_id)
    viz_service = VisualizationService(storage)

    stats = viz_service.get_event_stats()

    return EventStatsResponse(event_id=event_id, **stats)


@router.post(
    "/{event_id}/generate-crops",
    response_model=FaceCropsResponse,
    responses={404: {"model": ErrorResponse}},
)
async def generate_face_crops(
    event_id: str = PathParam(..., description="Event identifier"),
) -> FaceCropsResponse:
    """
    Extract and save all face crops for an event.
    Creates cropped images of each detected face.
    """
    if not StorageService.event_exists(event_id):
        raise HTTPException(status_code=404, detail="Event not found")

    storage = StorageService(event_id)
    viz_service = VisualizationService(storage)

    logger.info(f"Generating face crops for event {event_id}")
    face_crops = viz_service.save_face_crops()

    faces = [
        FaceCropInfo(
            face_id=crop["face_id"],
            photo_id=crop["photo_id"],
            bbox=crop["bbox"],
            crop_path=crop["crop_path"],
        )
        for crop in face_crops
    ]

    return FaceCropsResponse(event_id=event_id, faces=faces)


@router.get(
    "/{event_id}/faces/{face_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_face_crop(
    event_id: str = PathParam(..., description="Event identifier"),
    face_id: str = PathParam(..., description="Face identifier"),
):
    """
    Retrieve a face crop image by ID.
    Returns the cropped face image.
    """
    if not StorageService.event_exists(event_id):
        raise HTTPException(status_code=404, detail="Event not found")

    storage = StorageService(event_id)
    viz_service = VisualizationService(storage)

    crop_path = viz_service.get_face_crop_path(face_id)

    if not crop_path:
        raise HTTPException(status_code=404, detail="Face crop not found")

    return FileResponse(crop_path, media_type="image/jpeg")


@router.get(
    "/{event_id}/metadata",
    response_model=EventMetadataResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_event_metadata(
    event_id: str = PathParam(..., description="Event identifier"),
) -> EventMetadataResponse:
    """
    Get all face metadata for an event.
    Returns detailed information about each detected face.
    """
    if not StorageService.event_exists(event_id):
        raise HTTPException(status_code=404, detail="Event not found")

    storage = StorageService(event_id)
    metadata = storage.load_metadata()

    faces = [
        FaceMetadata(
            face_id=record["face_id"],
            photo_id=record["photo_id"],
            bbox=record["bbox"],
            embedding_id=record["embedding_id"],
        )
        for record in metadata
    ]

    return EventMetadataResponse(event_id=event_id, faces=faces)


@router.get(
    "/{event_id}/projections",
    response_model=ProjectionResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_embedding_projections(
    event_id: str = PathParam(..., description="Event identifier"),
) -> ProjectionResponse:
    """
    Get t-SNE 2D projection of face embeddings.
    Returns coordinates for visualizing embeddings in 2D space.
    """
    if not StorageService.event_exists(event_id):
        raise HTTPException(status_code=404, detail="Event not found")

    storage = StorageService(event_id)
    viz_service = VisualizationService(storage)

    logger.info(f"Computing t-SNE projections for event {event_id}")
    projections_data = viz_service.get_embedding_projection()

    projections = [
        EmbeddingProjection(
            face_id=proj["face_id"],
            photo_id=proj["photo_id"],
            x=proj["x"],
            y=proj["y"],
            embedding_id=proj["embedding_id"],
        )
        for proj in projections_data
    ]

    return ProjectionResponse(event_id=event_id, projections=projections)
