"""Pydantic schemas for API requests and responses."""
from typing import Optional
from pydantic import BaseModel, Field


# === Request Schemas ===

class TripCreateRequest(BaseModel):
    """Request to create a new trip from natural language (V1)."""
    user_message: str = Field(
        ..., 
        description="Natural language trip request from the user",
        examples=["I want to visit Paris for 5 days in June, love art and food"]
    )
    user_id: Optional[str] = Field(
        None,
        description="Optional user identifier for personalization"
    )


class TripConstraintsV2(BaseModel):
    """Structured constraints for V2 API."""
    origin: Optional[str] = None
    dates: Optional[dict] = None  # {start: str, end: str}
    travelers: Optional[dict] = None  # {adults: int, children: int}
    budget: Optional[str] = None
    pace: Optional[str] = None
    interests: Optional[str] = None  # Acts as prompt context
    amenities: list[str] = []


class TripCreateRequestV2(BaseModel):
    """Request to create a new trip with structured data (V2)."""
    destination: str
    constraints: Optional[TripConstraintsV2] = None


class TripUpdateRequest(BaseModel):
    """Request to update trip constraints."""
    additional_message: str = Field(
        ...,
        description="Additional user message to refine the trip"
    )


# === Response Schemas ===

class TripConstraintsResponse(BaseModel):
    """Trip constraints extracted by the Intake Agent."""
    destination: Optional[str] = None
    arrival_date: Optional[str] = None
    departure_date: Optional[str] = None
    num_people: Optional[int] = None
    budget: Optional[str] = None
    vibe: Optional[str] = None
    must_see: list[str] = []
    avoid: list[str] = []
    dietary_prefs: list[str] = []


class POIScoreBreakdown(BaseModel):
    """Breakdown of AI score components."""
    quality: float = Field(..., description="Score based on ratings (0-100)")
    popularity: float = Field(..., description="Score based on number of reviews (0-100)")
    price_fit: float = Field(..., description="How well it fits the budget (0-100)")
    user_match: Optional[float] = Field(None, description="Semantic match to user preferences (0-100)")
    proximity: Optional[float] = Field(None, description="Proximity to other POIs (0-100)")


class POIResponse(BaseModel):
    """A single Point of Interest with recommendation details."""
    place_id: str
    name: str
    category: list[str] = []
    rating: Optional[float] = None
    user_ratings_total: Optional[int] = None
    price_level: Optional[int] = None
    formatted_address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    website: Optional[str] = None
    opening_hours: Optional[dict] = None
    
    # AI Scoring
    ai_score: float = Field(..., description="Overall AI recommendation score (0-100)")
    score_breakdown: POIScoreBreakdown
    why_recommended: str = Field(..., description="Human-readable reason for recommendation")
    
    # Photos
    photo_reference: Optional[str] = Field(None, description="Reference to main photo")


class TripCreateResponse(BaseModel):
    """Response after creating a new trip."""
    trip_id: str
    constraints: TripConstraintsResponse
    message: str = Field(..., description="Summary message for the user")
    pois_found: int = Field(0, description="Number of POIs discovered")


class TripResponse(BaseModel):
    """Trip response for V2 API."""
    trip_id: str
    destination: str
    status: str
    current_stage: Optional[str]
    created_at: str
    updated_at: str


class TripPOIsResponse(BaseModel):
    """Response with all discovered POIs for a trip."""
    trip_id: str
    destination: Optional[str] = None
    destination_coords: Optional[dict] = None
    pois: list[POIResponse]
    total_pois: int = Field(..., description="Total number of POIs returned")


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = Field("healthy", description="Service status")
    phase: str = Field("1", description="Current development phase")
    services: dict = Field(
        default_factory=lambda: {
            "google_maps": "unknown",
            "gemini": "unknown"
        },
        description="Status of external services"
    )


class SemanticSearchRequest(BaseModel):
    """Semantic POI search request."""
    query: str
    limit: int = 20
    category: Optional[str] = None


class SemanticSearchResponse(BaseModel):
    """Semantic search response."""
    results: list[dict]
    total: int
    query: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str = Field(..., description="Error message")
    error_type: Optional[str] = Field(None, description="Type of error")
    trip_id: Optional[str] = Field(None, description="Trip ID if applicable")






