"""
Photo upload and retrieval endpoints.
"""

from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, File, HTTPException, Path as PathParam, UploadFile

from app.core.config import settings
from app.core.logging import get_logger
from app.domain.models import (
    AcceptedPhoto,
    ErrorResponse,
    RejectedPhoto,
    UploadPhotosResponse,
    UploadTotals,
)
from app.services.index import FaceIndexService
from app.services.pipeline import PipelineService
from app.services.storage import StorageService
from app.services.validation import ValidationError, validate_upload_file

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["photos"])


# Copilot: Implement bulk upload. For each file: validate -> save -> pipeline.ingest_photo().
# Return multi-status summary with accepted/rejected and totals.
@router.post(
    "/{event_id}/photos",
    response_model=UploadPhotosResponse,
    status_code=207,
    responses={404: {"model": ErrorResponse}},
)
async def upload_photos(
    event_id: str = PathParam(..., description="Event identifier"),
    files: list[UploadFile] = File(..., description="Photos to upload"),
) -> UploadPhotosResponse:
    """
    Upload photos to an event.
    Accepts multiple files, detects faces, and adds to the event index.
    Returns multi-status response with accepted/rejected files.
    """
    # Check if event exists
    if not StorageService.event_exists(event_id):
        raise HTTPException(status_code=404, detail="Event not found")

    # Initialize services
    storage = StorageService(event_id)
    index = FaceIndexService.create_for_event(storage.index_path)
    pipeline = PipelineService(storage, index)

    accepted: list[AcceptedPhoto] = []
    rejected: list[RejectedPhoto] = []
    total_faces = 0

    for file in files:
        try:
            # Validate file
            validate_upload_file(file)

            # Read file data
            content = await file.read()
            image_data = BytesIO(content)

            # Ingest photo
            result = pipeline.ingest_photo(image_data, file.filename or "unknown")

            accepted.append(
                AcceptedPhoto(
                    photo_id=result["photo_id"],
                    faces=result["face_count"],
                    path=result["path"],
                )
            )
            total_faces += result["face_count"]

        except ValidationError as e:
            logger.warning(f"Validation failed for {file.filename}: {e}")
            rejected.append(
                RejectedPhoto(
                    filename=file.filename or "unknown",
                    reason=str(e),
                )
            )
        except Exception as e:
            logger.error(f"Failed to process {file.filename}: {e}")
            rejected.append(
                RejectedPhoto(
                    filename=file.filename or "unknown",
                    reason=f"Processing error: {str(e)}",
                )
            )

    return UploadPhotosResponse(
        event_id=event_id,
        accepted=accepted,
        rejected=rejected,
        totals=UploadTotals(photos=len(accepted), faces=total_faces),
    )


@router.get(
    "/{event_id}/photos/{photo_id}",
    tags=["photos"],
    responses={404: {"model": ErrorResponse}},
)
async def get_photo(
    event_id: str = PathParam(..., description="Event identifier"),
    photo_id: str = PathParam(..., description="Photo identifier"),
):
    """
    Retrieve a photo by ID.
    Returns the image file.
    """
    if not StorageService.event_exists(event_id):
        raise HTTPException(status_code=404, detail="Event not found")

    storage = StorageService(event_id)

    try:
        return storage.serve_photo(photo_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Photo not found")
