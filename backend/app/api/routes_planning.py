"""
API endpoints for the interactive planning flow.
This router handles the sequential steps of the travel planning process.
"""
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel

from app.api.deps import get_current_user, get_current_user_or_guest
from app.services.google_maps import get_google_maps_service
from app.agents.discovery import discovery_agent
from app.agents.accommodation import AccommodationAgent
from app.models.state import TripConstraints

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/planning", tags=["planning"])

# In-memory storage for active planning sessions (to be replaced with DB later)
planning_sessions: Dict[str, Dict[str, Any]] = {}

# --- Request/Response Models ---

class PlanningStartRequest(BaseModel):
    query: str
    destination: str
    travelers: int
    budget: str
    interests: List[str]
    pace: str
    amenities: List[str]
    dates: Optional[str] = None
    tripStyle: Optional[str] = "balanced"
    origin: Optional[str] = None # Added origin field

class PlanningSessionResponse(BaseModel):
    session_id: str
    message: str

class DiscoverPlacesRequest(BaseModel):
    vibe: Optional[str] = None

class POISelectionRequest(BaseModel):
    selected_place_ids: List[str]

class AccommodationSearchRequest(BaseModel):
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    radius_km: Optional[int] = 10

class AccommodationSelectionRequest(BaseModel):
    selected_hotel_ids: List[str]
    hotel_data: Optional[Dict[str, Any]] = None

class TransportSelectionRequest(BaseModel):
    selected_transport_ids: List[str]

# --- Endpoints ---

@router.post("/start", response_model=PlanningSessionResponse)
async def start_planning(
    request: PlanningStartRequest,
    user_id: str = Depends(get_current_user_or_guest)
):
    """Initialize a new planning session."""
    session_id = str(uuid.uuid4())
    
    # Initialize session state
    planning_sessions[session_id] = {
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "initial_request": request.dict(),
        "constraints": {
            "destination": request.destination,
            "budget": request.budget,
            "travelers": request.travelers,
            "interests": request.interests,
            "pace": request.pace,
            "amenities": request.amenities,
            "dates": request.dates,
            "dates": request.dates,
            "vibe": request.tripStyle,
            "origin": request.origin # Store origin in constraints
        },
        "selections": {
            "pois": [],
            "accommodation": None,
            "dining": [],
            "transport": None,
            "activities": []
        },
        "discovered_data": {}
    }
    
    logger.info(f"Started planning session {session_id} for user {user_id}")
    
    return PlanningSessionResponse(
        session_id=session_id,
        message="Planning session started successfully"
    )

@router.post("/{session_id}/places/discover")
async def discover_places(
    session_id: str,
    request: DiscoverPlacesRequest = Body(default_factory=DiscoverPlacesRequest),
    user_id: str = Depends(get_current_user_or_guest)
):
    """Discover places to visit based on constraints."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    constraints = session["constraints"]
    
    # Update vibe if provided
    if request.vibe:
        constraints["vibe"] = request.vibe
        
    logger.info(f"Discovering places for session {session_id} in {constraints['destination']}")
    
    # Use existing discovery agent
    try:
        result = await discovery_agent(constraints)
        
        if result.get("error_message"):
            raise HTTPException(status_code=500, detail=result["error_message"])
            
        pois = result.get("potential_pois", [])
        
        # Store discovered POIs in session
        session["discovered_data"]["pois"] = pois
        
        # Enrich with photos
        pois = enrich_with_photos(pois)
        
        return {
            "pois": pois[:10], # Limit to top 10
            "summary": result.get("discovery_summary", "")
        }
        
    except Exception as e:
        logger.error(f"Error discovering places: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/places/select")
async def select_places(
    session_id: str,
    request: POISelectionRequest,
    user_id: str = Depends(get_current_user_or_guest)
):
    """Save user's selected places."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    discovered_pois = session["discovered_data"].get("pois", [])
    
    # Filter full POI objects based on selected IDs
    selected_pois = [
        poi for poi in discovered_pois 
        if poi.get("place_id") in request.selected_place_ids
    ]
    
    session["selections"]["pois"] = selected_pois
    logger.info(f"Session {session_id}: Selected {len(selected_pois)} places")
    
    return {"message": "Places selected successfully", "count": len(selected_pois)}

@router.post("/{session_id}/accommodations/search")
async def search_accommodations(
    session_id: str,
    request: AccommodationSearchRequest = Body(default_factory=AccommodationSearchRequest),
    user_id: str = Depends(get_current_user_or_guest)
):
    """Search for accommodations near selected places."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    constraints = session["constraints"]
    selected_pois = session["selections"].get("pois", [])
    
    agent = AccommodationAgent()
    
    # Determine search location
    # Priority: 1. Request coords, 2. Centroid of selected POIs, 3. Destination string
    location_coords = None
    
    if request.location_lat and request.location_lng:
        location_coords = {"lat": request.location_lat, "lng": request.location_lng}
    elif selected_pois:
        # Calculate centroid
        lats = [p.get("lat") for p in selected_pois if p.get("lat")]
        lngs = [p.get("lng") for p in selected_pois if p.get("lng")]
        if lats and lngs:
            location_coords = {
                "lat": sum(lats) / len(lats),
                "lng": sum(lngs) / len(lngs)
            }
            logger.info(f"Using centroid of {len(lats)} POIs for hotel search: {location_coords}")
    
    # Calculate dates (mock logic for now if not in constraints)
    from datetime import date, timedelta
    checkin = date.today() + timedelta(days=30)
    checkout = checkin + timedelta(days=3)
    
    try:
        hotels = await agent.search_hotels(
            destination=constraints["destination"],
            checkin_date=checkin,
            checkout_date=checkout,
            num_guests=constraints.get("travelers", 1),
            budget_preference=constraints.get("budget", "moderate"),
            location_coords=location_coords,
            radius_km=request.radius_km or 10
        )
        
        # Score hotels
        # We need to pass POIs to calculate location score
        pois_for_scoring = selected_pois if selected_pois else []
        
        scored_hotels = []
        avg_price = sum(h.total_price for h in hotels) / len(hotels) if hotels else 0
        
        for hotel in hotels:
            # Calculate scores
            loc_score = await agent.calculate_location_score(hotel, pois_for_scoring)
            price_score = await agent.calculate_price_value_score(hotel, constraints.get("budget", "moderate"), avg_price)
            await agent.calculate_overall_score(hotel, loc_score, price_score)
            scored_hotels.append(hotel.__dict__) # Convert to dict
            
        # Sort by score
        scored_hotels.sort(key=lambda x: x.get("ai_score", 0), reverse=True)
        
        session["discovered_data"]["hotels"] = scored_hotels
        
        # Enrich with photos
        scored_hotels = enrich_with_photos(scored_hotels)
        
        return {
            "hotels": scored_hotels[:10], # Limit to top 10
            "summary": f"Found {len(scored_hotels)} hotels near your selected activities."
        }
        
    except Exception as e:
        logger.error(f"Error searching accommodations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/accommodations/select")
async def select_accommodation(
    session_id: str,
    request: AccommodationSelectionRequest,
    user_id: str = Depends(get_current_user_or_guest)
):
    """Save user's selected accommodation."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    
    # If hotel data is provided directly, use it (useful if frontend has full object)
    if request.hotel_data:
        # Append to list if not present (simple logic for now)
        current_selections = session["selections"].get("accommodation", [])
        if not isinstance(current_selections, list):
            current_selections = [current_selections] if current_selections else []
            
        current_selections.append(request.hotel_data)
        session["selections"]["accommodation"] = current_selections
    else:
        # Look up in discovered hotels
        discovered_hotels = session["discovered_data"].get("hotels", [])
        
        selected_hotels = [
            h for h in discovered_hotels 
            if h.get("hotel_id") in request.selected_hotel_ids or 
               h.get("id") in request.selected_hotel_ids or
               h.get("provider_id") in request.selected_hotel_ids
        ]
        
        if selected_hotels:
            session["selections"]["accommodation"] = selected_hotels
            logger.info(f"Session {session_id}: Selected {len(selected_hotels)} hotels")
        else:
            logger.warning(f"Selected hotels {request.selected_hotel_ids} not found in session data")
            
    return {"message": "Accommodation selected successfully"}

# Placeholder endpoints for other sections to complete the flow
@router.post("/{session_id}/dining/search")
async def search_dining(session_id: str, user_id: str = Depends(get_current_user_or_guest)):
    """Search for dining options using AI-generated queries."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    constraints = session["constraints"]
    
    try:
        # 1. Generate Queries
        from app.agents.query_generator import QueryGenerator
        query_gen = QueryGenerator()
        queries = await query_gen.generate_queries("dining", constraints["destination"], constraints)
        
        # 2. Run Discovery with these queries
        # We reuse the discovery agent but pass specific queries
        discovery_constraints = constraints.copy()
        discovery_constraints["search_queries"] = queries
        
        # We want to ensure we filter out non-restaurants
        # The discovery agent's LLM filter is generic "attractions", we might need to adjust it or trust the query.
        # For now, the "strict location validator" in discovery.py removes "Travel Agencies", which is good.
        # We might want to add a "category" to discovery_agent to switch the validator prompt?
        # For now, let's rely on the query being specific ("restaurants in ...").
        
        result = await discovery_agent(discovery_constraints)
        
        if result.get("error_message"):
            raise HTTPException(status_code=500, detail=result["error_message"])
            
        restaurants = result.get("potential_pois", [])
        
        # Store discovered dining
        session["discovered_data"]["dining"] = restaurants
        
        # Enrich with photos
        restaurants = enrich_with_photos(restaurants)
        
        return {
            "restaurants": restaurants[:10],
            "summary": result.get("discovery_summary", "")
        }
        
    except Exception as e:
        logger.error(f"Error searching dining: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/transport/search")
async def search_transport(session_id: str, user_id: str = Depends(get_current_user_or_guest)):
    """Search for transport options (flights/trains + local)."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    constraints = session["constraints"]
    
    # We need to construct a state object for the TransportAgent
    # In a real LangGraph flow, this would be passed automatically.
    # Here we mock the state for the agent node.
    from app.models.state import TravelAgentState
    
    state = TravelAgentState(
        constraints=constraints,
        potential_pois=session["discovered_data"].get("pois", []),
        recommended_hotels=session["discovered_data"].get("hotels", [])
    )
    
    try:
        from app.agents.transport import transport_agent_node
        result = await transport_agent_node(state)
        
        transport_data = {
            "flights": result.get("recommended_flights", []),
            "local": result.get("local_transport", {}),
            "summary": "\n".join(result.get("messages", []))
        }
        
        session["discovered_data"]["transport"] = transport_data
        
        return {
            "transport_options": transport_data,
            "summary": transport_data["summary"]
        }
        
    except Exception as e:
        logger.error(f"Error searching transport: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/transport/select")
async def select_transport(
    session_id: str,
    request: TransportSelectionRequest,
    user_id: str = Depends(get_current_user_or_guest)
):
    """Save user's selected transport options."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    discovered_transport = session["discovered_data"].get("transport", {})
    
    # Flatten discovered options for lookup
    all_options = []
    if "flights" in discovered_transport:
        all_options.extend(discovered_transport["flights"])
    
    # Local transport is a bit complex, it might be a dict or list
    # For now, we just store the IDs as the selection, or try to find them if possible
    # But since transport selection in frontend is just IDs, we might just store IDs
    # However, ItineraryAgent needs details.
    
    # Let's try to find the selected objects
    selected_objects = []
    for tid in request.selected_transport_ids:
        # Check flights
        found = False
        for f in discovered_transport.get("flights", []):
            # Flight ID might be offer_id or id
            if f.get("offer_id") == tid or f.get("id") == tid:
                selected_objects.append(f)
                found = True
                break
        
        if not found:
            # Check local transport (if it's a list in discovered_data)
            # The structure of local_transport in discovered_data is:
            # { "mode_comparison": {...}, "transit_options": [...], ... }
            # But frontend maps them to "local-type-index".
            # This is hard to map back.
            # For local transport, we might just store the ID and let ItineraryAgent handle it (or ignore it).
            # OR we can just store the ID.
            selected_objects.append({"id": tid, "type": "local_transport_placeholder"})

    session["selections"]["transport"] = selected_objects
    logger.info(f"Session {session_id}: Selected {len(selected_objects)} transport options")
    
    return {"message": "Transport selected successfully"}

@router.post("/{session_id}/activities/search")
async def search_activities(session_id: str, user_id: str = Depends(get_current_user_or_guest)):
    """Search for activities using AI-generated queries."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    constraints = session["constraints"]
    
    try:
        # 1. Generate Queries
        from app.agents.query_generator import QueryGenerator
        query_gen = QueryGenerator()
        queries = await query_gen.generate_queries("activities", constraints["destination"], constraints)
        
        # 2. Run Discovery
        discovery_constraints = constraints.copy()
        discovery_constraints["search_queries"] = queries
        
        result = await discovery_agent(discovery_constraints)
        
        if result.get("error_message"):
            raise HTTPException(status_code=500, detail=result["error_message"])
            
        activities = result.get("potential_pois", [])
        
        # Store discovered activities
        session["discovered_data"]["activities"] = activities
        
        # Enrich with photos
        activities = enrich_with_photos(activities)
        
        return {
            "activities": activities[:10],
            "summary": result.get("discovery_summary", "")
        }
        
    except Exception as e:
        logger.error(f"Error searching activities: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/shopping/search")
async def search_shopping(session_id: str, user_id: str = Depends(get_current_user_or_guest)):
    """Search for shopping and markets using AI-generated queries."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    constraints = session["constraints"]
    
    try:
        # 1. Generate Queries
        from app.agents.query_generator import QueryGenerator
        query_gen = QueryGenerator()
        queries = await query_gen.generate_queries("shopping", constraints["destination"], constraints)
        
        # 2. Run Discovery
        discovery_constraints = constraints.copy()
        discovery_constraints["search_queries"] = queries
        
        result = await discovery_agent(discovery_constraints)
        
        if result.get("error_message"):
            raise HTTPException(status_code=500, detail=result["error_message"])
            
        shopping_spots = result.get("potential_pois", [])
        
        # Store discovered shopping
        session["discovered_data"]["shopping"] = shopping_spots
        
        # Enrich with photos
        shopping_spots = enrich_with_photos(shopping_spots)
        
        return {
            "shopping": shopping_spots[:10],
            "summary": result.get("discovery_summary", "")
        }
        
    except Exception as e:
        logger.error(f"Error searching shopping: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{session_id}/wellness/search")
async def search_wellness(session_id: str, user_id: str = Depends(get_current_user_or_guest)):
    """Search for wellness options using AI-generated queries."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    constraints = session["constraints"]
    
    try:
        # 1. Generate Queries
        from app.agents.query_generator import QueryGenerator
        query_gen = QueryGenerator()
        queries = await query_gen.generate_queries("wellness", constraints["destination"], constraints)
        
        # 2. Run Discovery
        discovery_constraints = constraints.copy()
        discovery_constraints["search_queries"] = queries
        
        result = await discovery_agent(discovery_constraints)
        
        if result.get("error_message"):
            raise HTTPException(status_code=500, detail=result["error_message"])
            
        wellness_spots = result.get("potential_pois", [])
        
        # Store discovered wellness
        session["discovered_data"]["wellness"] = wellness_spots
        
        # Enrich with photos
        wellness_spots = enrich_with_photos(wellness_spots)
        
        return {
            "wellness_options": wellness_spots[:10],
            "summary": result.get("discovery_summary", "")
        }
        
    except Exception as e:
        logger.error(f"Error searching wellness: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from fastapi.responses import RedirectResponse
from app.config import settings

# Helper to add photo URLs
def enrich_with_photos(pois: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    base_url = f"http://{settings.host}:{settings.port}" if settings.environment == "development" else "https://api.yourdomain.com"
    # Fallback if settings not set correctly
    if "0.0.0.0" in base_url:
        base_url = "http://127.0.0.1:8000"
        
    for poi in pois:
        if "photos" in poi and poi["photos"]:
            ref = poi["photos"][0].get("photo_reference")
            if ref:
                poi["photo_url"] = f"{base_url}/api/v2/planning/photos/{ref}"
    return pois

@router.get("/photos/{reference}")
async def get_photo(reference: str):
    """Proxy for Google Places Photo API to hide API key."""
    url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={reference}&key={settings.google_maps_api_key}"
    return RedirectResponse(url)

# --- Selection Requests ---

class DiningSelectionRequest(BaseModel):
    selected_dining_ids: List[str]

class ActivitySelectionRequest(BaseModel):
    selected_activity_ids: List[str]

class ShoppingSelectionRequest(BaseModel):
    selected_shopping_ids: List[str]

class WellnessSelectionRequest(BaseModel):
    selected_wellness_ids: List[str]

class AccommodationSelectionRequest(BaseModel):
    selected_accommodation_ids: List[str]

# --- Selection Endpoints ---

@router.post("/{session_id}/dining/select")
async def select_dining(
    session_id: str,
    request: DiningSelectionRequest,
    user_id: str = Depends(get_current_user_or_guest)
):
    """Save user's selected dining options."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    discovered = session["discovered_data"].get("dining", [])
    
    selected = [
        item for item in discovered 
        if item.get("place_id") in request.selected_dining_ids
    ]
    
    session["selections"]["dining"] = selected
    logger.info(f"Session {session_id}: Selected {len(selected)} dining options")
    return {"message": "Dining selected successfully"}

@router.post("/{session_id}/activities/select")
async def select_activities(
    session_id: str,
    request: ActivitySelectionRequest,
    user_id: str = Depends(get_current_user_or_guest)
):
    """Save user's selected activities."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    discovered = session["discovered_data"].get("activities", [])
    
    selected = [
        item for item in discovered 
        if item.get("place_id") in request.selected_activity_ids
    ]
    
    session["selections"]["activities"] = selected
    logger.info(f"Session {session_id}: Selected {len(selected)} activities")
    return {"message": "Activities selected successfully"}

@router.post("/{session_id}/shopping/select")
async def select_shopping(
    session_id: str,
    request: ShoppingSelectionRequest,
    user_id: str = Depends(get_current_user_or_guest)
):
    """Save user's selected shopping options."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    discovered = session["discovered_data"].get("shopping", [])
    
    selected = [
        item for item in discovered 
        if item.get("place_id") in request.selected_shopping_ids
    ]
    
    session["selections"]["shopping"] = selected
    logger.info(f"Session {session_id}: Selected {len(selected)} shopping options")
    return {"message": "Shopping selected successfully"}

@router.post("/{session_id}/wellness/select")
async def select_wellness(
    session_id: str,
    request: WellnessSelectionRequest,
    user_id: str = Depends(get_current_user_or_guest)
):
    """Save user's selected wellness options."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    discovered = session["discovered_data"].get("wellness", [])
    
    selected = [
        item for item in discovered 
        if item.get("place_id") in request.selected_wellness_ids
    ]
    
    session["selections"]["wellness"] = selected
    logger.info(f"Session {session_id}: Selected {len(selected)} wellness options")
    return {"message": "Wellness selected successfully"}

@router.post("/{session_id}/accommodation/select")
async def select_accommodation(
    session_id: str,
    request: AccommodationSelectionRequest,
    user_id: str = Depends(get_current_user_or_guest)
):
    """Save user's selected accommodation."""
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = planning_sessions[session_id]
    # Accommodations might be in "hotels" key in discovered_data
    discovered = session["discovered_data"].get("hotels", [])
    
    selected = [
        item for item in discovered 
        if item.get("hotel_id") in request.selected_accommodation_ids or item.get("id") in request.selected_accommodation_ids
    ]
    
    # Store as a list, even if it's usually one
    session["selections"]["accommodation"] = selected
    logger.info(f"Session {session_id}: Selected {len(selected)} accommodation options")
    return {"message": "Accommodation selected successfully"}

@router.post("/{session_id}/itinerary/generate")
async def generate_itinerary(session_id: str, user_id: str = Depends(get_current_user_or_guest)):
    if session_id not in planning_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = planning_sessions[session_id]
    
    try:
        from app.agents.itinerary import ItineraryAgent
        agent = ItineraryAgent()
        
        itinerary = await agent.generate_itinerary(session)
        
        return itinerary
        
    except Exception as e:
        logger.error(f"Error generating itinerary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
