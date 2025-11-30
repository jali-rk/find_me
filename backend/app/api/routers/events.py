"""
Event creation endpoint.
"""

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.domain.models import CreateEventResponse, ErrorResponse
from app.services.storage import StorageService
from app.utils.ids import generate_event_id

router = APIRouter(prefix="/events", tags=["events"])


# Copilot: Implement POST /events to create a new event folder using storage service and return ids.
@router.post(
    "",
    response_model=CreateEventResponse,
    status_code=201,
    responses={500: {"model": ErrorResponse}},
)
async def create_event() -> CreateEventResponse:
    """
    Create a new event.
    Generates a unique event ID and creates the directory structure.
    """
    # Ensure data directory exists
    settings.ensure_data_dir()

    # Generate event ID
    event_id = generate_event_id()

    # Create event storage
    storage = StorageService.create_event(event_id)

    return CreateEventResponse(
        event_id=event_id,
        data_dir=str(storage.event_dir),
    )
