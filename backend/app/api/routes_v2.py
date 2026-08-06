"""
Phase 2.2 API Routes - Database & Vector Search
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.config import settings
from app.db import get_session
from app.services.database import DatabaseService
from app.services.state_persistence import StatePersistenceService
from app.services.vector_store import get_vector_store_service
from app.models.state import TravelAgentState

logger = logging.getLogger(__name__)

router_v2 = APIRouter(prefix="/api/v2", tags=["Phase 2.2"])
security = HTTPBearer()

# ==================== Request/Response Models ====================

class UserRegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    preferences: Optional[dict] = None

class UserLoginRequest(BaseModel):
    """User login request."""
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    """Authentication response."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str

from app.models.schemas import TripCreateRequestV2, TripResponse, SemanticSearchRequest, SemanticSearchResponse
from app.agents.graph import get_travel_agent_graph
from langchain_core.messages import HumanMessage
import uuid
from app.api.deps import get_current_user, create_access_token

# ==================== Auth Endpoints ====================

@router_v2.post("/auth/register", response_model=AuthResponse)
async def register(
    request: UserRegisterRequest,
    session: AsyncSession = Depends(get_session)
):
    """Register a new user."""
    db = DatabaseService(session)
    
    # Check if user exists
    existing_user = await db.get_user_by_email(request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = await db.create_user(
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        preferences=request.preferences
    )
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return AuthResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email
    )

@router_v2.post("/auth/login", response_model=AuthResponse)
async def login(
    request: UserLoginRequest,
    session: AsyncSession = Depends(get_session)
):
    """Login user."""
    db = DatabaseService(session)
    
    # Get user
    user = await db.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not await db.verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create token
    access_token = create_access_token(data={"sub": user.id})
    
    return AuthResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email
    )

# ... (keep other models)

@router_v2.post("/trips", response_model=TripResponse)
async def create_trip(
    request: TripCreateRequestV2,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new trip (V2).
    
    Initializes a trip with structured destination and constraints.
    Triggers the LangGraph workflow with the structured data.
    """
    db = DatabaseService(session)
    trip_id = str(uuid.uuid4())
    
    # Create initial state for Graph
    # We construct a synthetic user message from the structured data for the Intake agent (hybrid approach)
    # But we also pass the raw constraints so Intake can just use them.
    
    constraints_dict = request.constraints.model_dump() if request.constraints else {}
    constraints_dict['destination'] = request.destination
    
    # Create a prompt-like message for context
    interests = constraints_dict.get('interests', '')
    user_message = f"Trip to {request.destination}. Interests: {interests}"
    
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "current_stage": "start",
        "constraints": constraints_dict,  # Pass structured constraints directly
        "potential_pois": [],
        "itinerary": [],
        "available_hotels": [],
        "trip_id": trip_id,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Run the graph
    logger.info(f"Running graph for trip {trip_id} (V2)...")
    graph = get_travel_agent_graph()
    result = await graph.ainvoke(initial_state)
    
    # Extract results
    final_constraints = result.get('constraints', {})
    
    # Persist to DB
    trip = await db.create_trip(
        user_id=user_id,
        trip_id=trip_id,
        destination=request.destination,
        constraints=final_constraints,
        destination_lat=result.get('destination_coords', {}).get('lat'),
        destination_lng=result.get('destination_coords', {}).get('lng')
    )
    
    # Save full state
    persistence = StatePersistenceService(session)
    await persistence.save_trip_state(trip_id, result)
    
    logger.info(f"Created trip {trip.id} for user {user_id}")
    
    return TripResponse(
        trip_id=trip.id,
        destination=trip.destination,
        status=trip.status,
        current_stage=trip.current_stage,
        created_at=trip.created_at.isoformat(),
        updated_at=trip.updated_at.isoformat()
    )

@router_v2.get("/trips", response_model=List[TripResponse])
async def list_user_trips(
    status: Optional[str] = None,
    limit: int = 50,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    List user's trips.
    
    Optionally filter by status (planning, optimized, booked, completed).
    """
    db = DatabaseService(session)
    
    trips = await db.get_user_trips(user_id, status=status, limit=limit)
    
    return [
        TripResponse(
            trip_id=trip.id,
            destination=trip.destination,
            status=trip.status,
            current_stage=trip.current_stage,
            created_at=trip.created_at.isoformat(),
            updated_at=trip.updated_at.isoformat()
        )
        for trip in trips
    ]

@router_v2.get("/trips/{trip_id}")
async def get_trip(
    trip_id: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get trip details.
    
    Returns full trip information including POIs and itinerary.
    """
    db = DatabaseService(session)
    
    trip = await db.get_trip_by_id(trip_id, include_itinerary=True, include_pois=True)
    if not trip or trip.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Get itinerary
    itinerary = await db.get_trip_itinerary(trip_id)
    
    # Get POIs
    trip_pois = await db.get_trip_pois(trip_id)
    
    return {
        "trip_id": trip.id,
        "destination": trip.destination,
        "status": trip.status,
        "current_stage": trip.current_stage,
        "constraints": trip.constraints,
        "created_at": trip.created_at.isoformat(),
        "updated_at": trip.updated_at.isoformat(),
        "itinerary": [
            {
                "poi_name": item.poi.name if item.poi else "Starting Point",
                "start_time": item.start_time,
                "end_time": item.end_time,
                "visit_duration_minutes": item.visit_duration_minutes,
                "travel_time_to_next_minutes": item.travel_time_to_next_minutes
            }
            for item in itinerary
        ],
        "discovered_pois": [
            {
                "name": tp.poi.name,
                "place_id": tp.poi.place_id,
                "ai_score": tp.ai_score,
                "user_selected": tp.user_selected,
                "recommendation_reason": tp.recommendation_reason
            }
            for tp in trip_pois
        ]
    }

@router_v2.post("/trips/{trip_id}/save-state")
async def save_trip_state(
    trip_id: str,
    state: dict,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Save trip state from LangGraph workflow.
    
    This enables session resumption and state persistence.
    """
    db = DatabaseService(session)
    
    # Verify trip ownership
    trip = await db.get_trip_by_id(trip_id)
    if not trip or trip.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Save state
    persistence = StatePersistenceService(session)
    success = await persistence.save_trip_state(trip_id, state)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save trip state"
        )
    
    return {"status": "saved", "trip_id": trip_id}

@router_v2.get("/trips/{trip_id}/load-state")
async def load_trip_state(
    trip_id: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Load trip state for resuming workflow.
    
    Returns the full LangGraph state.
    """
    db = DatabaseService(session)
    
    # Verify trip ownership
    trip = await db.get_trip_by_id(trip_id)
    if not trip or trip.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    # Load state
    persistence = StatePersistenceService(session)
    state = await persistence.load_trip_state(trip_id)
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No state found for this trip"
        )
    
    return {"trip_id": trip_id, "state": state}

@router_v2.delete("/trips/{trip_id}")
async def delete_trip(
    trip_id: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Delete a trip."""
    db = DatabaseService(session)
    
    # Verify trip ownership
    trip = await db.get_trip_by_id(trip_id)
    if not trip or trip.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trip not found"
        )
    
    success = await db.delete_trip(trip_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete trip"
        )
    
    return {"status": "deleted", "trip_id": trip_id}

# ==================== Semantic Search Endpoints ====================

@router_v2.post("/pois/semantic-search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Semantic search for POIs.
    
    Uses vector embeddings to find POIs matching the natural language query.
    
    Examples:
    - "quiet cafes with good wifi"
    - "romantic restaurants with sunset views"
    - "hidden gem art galleries"
    """
    try:
        vector_store = get_vector_store_service()
        
        results = await vector_store.search_similar_pois(
            query=request.query,
            limit=request.limit,
            category_filter=request.category
        )
        
        return SemanticSearchResponse(
            results=results,
            total=len(results),
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Semantic search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Semantic search unavailable"
        )

@router_v2.get("/pois/stats")
async def get_poi_stats(user_id: str = Depends(get_current_user)):
    """Get vector store statistics."""
    try:
        vector_store = get_vector_store_service()
        
        total_pois = await vector_store.count_pois()
        
        return {
            "total_indexed_pois": total_pois,
            "collection": vector_store.collection_name,
            "status": "operational"
        }
        
    except Exception as e:
        logger.error(f"Failed to get POI stats: {e}")
        return {
            "total_indexed_pois": 0,
            "status": "unavailable",
            "error": str(e)
        }

# ==================== User Analytics ====================

@router_v2.get("/users/me/stats")
async def get_user_stats(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get user statistics."""
    db = DatabaseService(session)
    
    stats = await db.get_user_stats(user_id)
    
    return stats
















@router_v2.get("/users/me", response_model=AuthResponse)
async def read_users_me(
    current_user: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """Get current user details."""
    db = DatabaseService(session)
    user = await db.get_user_by_id(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # We return AuthResponse structure for consistency with login/register
    # but without a new token (unless we want to refresh it)
    return AuthResponse(
        access_token="", # Not needed for profile fetch
        user_id=user.id,
        email=user.email
    )

