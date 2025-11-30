"""
Pydantic response models for Health, CreateEvent, UploadSummary, MatchResult.
Domain schemas for API contracts.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# Health
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="ok", description="Service health status")


# Events
class CreateEventResponse(BaseModel):
    """Response for creating a new event."""

    event_id: str = Field(description="Unique event identifier (ULID)")
    data_dir: str = Field(description="Path to event data directory")


# Photos
class AcceptedPhoto(BaseModel):
    """Details of a successfully processed photo."""

    photo_id: str = Field(description="Unique photo identifier (ULID)")
    faces: int = Field(ge=0, description="Number of faces detected")
    path: str = Field(description="Relative path to the photo file")


class RejectedPhoto(BaseModel):
    """Details of a rejected photo."""

    filename: str = Field(description="Original filename")
    reason: str = Field(description="Rejection reason")


class UploadTotals(BaseModel):
    """Summary totals for upload operation."""

    photos: int = Field(ge=0, description="Total photos accepted")
    faces: int = Field(ge=0, description="Total faces detected across all photos")


class UploadPhotosResponse(BaseModel):
    """Multi-status response for bulk photo upload."""

    event_id: str = Field(description="Event identifier")
    accepted: list[AcceptedPhoto] = Field(default_factory=list, description="Successfully processed photos")
    rejected: list[RejectedPhoto] = Field(default_factory=list, description="Rejected photos")
    totals: UploadTotals = Field(description="Summary totals")


# Match
class MatchResult(BaseModel):
    """A single photo match result."""

    photo_id: str = Field(description="Photo identifier")
    path: str = Field(description="Relative path to the photo")
    score: float = Field(ge=0.0, le=1.0, description="Similarity score (cosine)")
    bbox: list[int] = Field(description="Bounding box [x, y, w, h] in pixels")


class MatchResponse(BaseModel):
    """Response for selfie matching."""

    event_id: str = Field(description="Event identifier")
    results: list[MatchResult] = Field(default_factory=list, description="Matched photos sorted by score")


# Error
class ErrorDetail(BaseModel):
    """Structured error detail."""

    code: str = Field(description="Error code")
    message: str = Field(description="Human-readable error message")


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: ErrorDetail = Field(description="Error details")
