"""
Selfie matching endpoint.
"""

from __future__ import annotations

from collections import defaultdict
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, Path as PathParam, UploadFile

from app.core.config import settings
from app.core.logging import get_logger
from app.domain.models import ErrorResponse, MatchResponse, MatchResult
from app.services.face import get_face_service
from app.services.index import FaceIndexService
from app.services.storage import StorageService
from app.services.validation import ValidationError, validate_upload_file
from app.utils.images import safe_open_image

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["match"])


# Copilot: Implement selfie match endpoint. Detect faces from memory stream, run index.search per embedding,
# aggregate per photo_id (max score), threshold filter, sort desc, return top N.
@router.post(
    "/{event_id}/match",
    response_model=MatchResponse,
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
)
async def match_selfie(
    event_id: str = PathParam(..., description="Event identifier"),
    selfie: UploadFile = File(..., description="Selfie image for matching"),
) -> MatchResponse:
    """
    Match a selfie against event photos.
    Detects faces in the selfie, searches the event index, and returns matching photos
    sorted by similarity score.
    """
    # Check if event exists
    if not StorageService.event_exists(event_id):
        raise HTTPException(status_code=404, detail="Event not found")

    # Initialize services
    storage = StorageService(event_id)
    index = FaceIndexService.create_for_event(storage.index_path)
    face_service = get_face_service()

    # Validate selfie
    try:
        validate_upload_file(selfie)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Read and process selfie image (do not save to disk)
    content = await selfie.read()
    image_data = BytesIO(content)

    try:
        image = safe_open_image(image_data, max_size=2000)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    # Detect faces in selfie
    faces = face_service.detect_and_embed(image)

    if not faces:
        logger.info("No faces detected in selfie")
        return MatchResponse(event_id=event_id, results=[])

    if index.size() == 0:
        logger.info("Index is empty, no matches possible")
        return MatchResponse(event_id=event_id, results=[])

    logger.info(f"Detected {len(faces)} faces in selfie, searching index")

    # Load metadata for mapping embedding IDs to photos
    metadata_records = storage.load_metadata()

    if not metadata_records:
        logger.info("No metadata found")
        return MatchResponse(event_id=event_id, results=[])

    # Search for each face in selfie
    all_matches: dict[str, dict] = {}  # photo_id -> best match info

    for face_idx, face in enumerate(faces):
        query_embedding = face["embedding"].reshape(1, -1)

        # Search index
        scores, ids = index.search(query_embedding, k=100)

        # Process results for this face
        for score, embedding_id in zip(scores[0], ids[0]):
            # Filter by threshold
            if score < settings.face_match_threshold:
                continue

            # Find metadata for this embedding
            for record in metadata_records:
                if record["embedding_id"] == int(embedding_id):
                    photo_id = record["photo_id"]

                    # Keep best score per photo
                    if photo_id not in all_matches or score > all_matches[photo_id]["score"]:
                        all_matches[photo_id] = {
                            "photo_id": photo_id,
                            "path": record["path"],
                            "score": float(score),
                            "bbox": record["bbox"],
                        }
                    break

    # Sort by score descending
    sorted_matches = sorted(
        all_matches.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    # Convert to response format
    results = [
        MatchResult(
            photo_id=match["photo_id"],
            path=match["path"],
            score=match["score"],
            bbox=match["bbox"],
        )
        for match in sorted_matches
    ]

    logger.info(f"Found {len(results)} matching photos")

    return MatchResponse(event_id=event_id, results=results)
