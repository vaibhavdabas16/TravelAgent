"""LangGraph state definitions for the travel agent.

These TypedDicts define the structure of data that flows through
the agent's reasoning process.
"""
from typing import TypedDict, Annotated, Optional
from langgraph.graph.message import add_messages


class TripConstraints(TypedDict, total=False):
    """Trip constraints extracted from user input by the Intake Agent."""
    destination: Optional[str]
    arrival_date: Optional[str]  # YYYY-MM-DD format
    departure_date: Optional[str]  # YYYY-MM-DD format
    num_people: Optional[int]
    budget: Optional[str]  # "budget", "moderate", "luxury"
    vibe: Optional[str]  # "relaxed", "adventurous", "cultural", "family", etc.
    must_see: list[str]  # Specific places the user wants to visit
    avoid: list[str]  # Things to avoid
    dietary_prefs: list[str]  # Dietary preferences/restrictions


class POI(TypedDict, total=False):
    """Point of Interest with Google Places data and AI scoring."""
    # Google Places fields
    place_id: str
    name: str
    formatted_address: Optional[str]
    geometry: Optional[dict]  # Contains 'location' with lat/lng
    categories: list[str]  # From 'types' field
    rating: Optional[float]
    user_ratings_total: Optional[int]
    price_level: Optional[int]  # 0-4 scale
    opening_hours: Optional[dict]
    website: Optional[str]
    photos: Optional[list]
    reviews: Optional[list]
    
    # Computed fields
    lat: Optional[float]
    lng: Optional[float]
    
    # AI Scoring fields
    ai_score: Optional[float]  # 0-100
    score_breakdown: Optional[dict]  # Individual score components
    recommendation_reason: Optional[str]  # Why this was recommended


class ItineraryItem(TypedDict, total=False):
    """A scheduled item in the user's itinerary (Phase 2)."""
    place_name: str
    place_id: str
    address: str
    start_time: str  # ISO format datetime or HH:MM
    end_time: str  # ISO format datetime or HH:MM
    notes: Optional[str]
    travel_time_to_next: Optional[int]  # Minutes
    visit_duration_minutes: Optional[int]


class OptimizationParameters(TypedDict, total=False):
    """Parameters for itinerary optimization."""
    day_start_hour: int  # 0-23
    day_end_hour: int  # 0-23
    travel_mode: str  # "walking", "driving", "transit", "bicycling"
    strict_mode: bool  # If True, constraints are non-negotiable
    optimization_goal: str  # "fastest", "balanced", "relaxed"


class OptimizationSuggestion(TypedDict, total=False):
    """Suggestions when optimization fails."""
    suggestion_type: str  # "extend_hours", "reduce_pois", "change_mode"
    original_value: str
    suggested_value: str
    reason: str
    feasibility_score: float  # 0-1, how likely this will work


class TravelAgentState(TypedDict, total=False):
    """
    Complete state for the Travel Agent LangGraph.
    
    This state is passed through all nodes in the graph and accumulates
    information as the agent processes the user's request.
    """
    # Conversation history (managed by LangGraph)
    messages: Annotated[list, add_messages]
    
    # Trip context
    constraints: Optional[TripConstraints]
    destination_coords: Optional[dict]  # {'lat': float, 'lng': float, 'formatted_address': str}
    
    # Discovered POIs
    potential_pois: list[POI]  # All discovered POIs (scored but not scheduled)
    
    # Optimized itinerary (Phase 2)
    itinerary: list[ItineraryItem]
    optimization_params: Optional[OptimizationParameters]
    optimization_suggestions: list[OptimizationSuggestion]  # When optimization fails
    optimization_attempts: int  # Track retry attempts
    
    # Accommodations (Phase 2)
    available_hotels: list[dict]
    
    # Accommodation & Transport (Phase 2.3 - Week 4)
    recommended_hotels: Optional[list[dict]]  # List of Hotel dicts with AI scores
    recommended_flights: Optional[list[dict]]  # List of Flight dicts with AI scores
    local_transport: Optional[dict]  # Local transport analysis and recommendations
    
    # Control flow
    current_stage: str  # "start", "intake_complete", "discovery_complete", "optimization_complete", etc.
    error_message: Optional[str]
    
    # Metadata
    trip_id: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

