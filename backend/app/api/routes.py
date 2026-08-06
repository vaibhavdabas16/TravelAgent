"""REST API endpoints for the travel agent."""
import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from langchain_core.messages import HumanMessage

from app.models.schemas import (
    TripCreateRequest,
    TripCreateResponse,
    TripPOIsResponse,
    POIResponse,
    POIScoreBreakdown,
    TripConstraintsResponse,
    HealthCheckResponse,
    ErrorResponse
)
from app.agents.graph import get_travel_agent_graph
from app.services.google_maps import get_google_maps_service
from app.services.gemini import get_gemini_service

from app.api.deps import get_current_user
from app.db import get_session_context
from app.services.database import DatabaseService
from app.services.state_persistence import StatePersistenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["trips"])


# In-memory storage for Phase 1 (will be replaced with database in Phase 2)
trips_store = {}


@router.post("/trips", response_model=TripCreateResponse, responses={500: {"model": ErrorResponse}})
async def create_trip(
    request: TripCreateRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new trip from natural language input.
    
    This endpoint processes the user's trip description, extracts constraints,
    and discovers relevant POIs using the LangGraph workflow.
    
    - **user_message**: Natural language description of the trip
    - **user_id**: Authenticated user ID
    
    Returns the trip ID, extracted constraints, and number of POIs found.
    """
    try:
        trip_id = str(uuid.uuid4())
        logger.info(f"Creating trip {trip_id} from message: {request.user_message[:100]}...")
        
        # Get the graph
        graph = get_travel_agent_graph()
        
        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=request.user_message)],
            "current_stage": "start",
            "potential_pois": [],
            "itinerary": [],
            "available_hotels": [],
            "trip_id": trip_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Run the graph
        logger.info(f"Running graph for trip {trip_id}...")
        result = await graph.ainvoke(initial_state)
        
        # Check for errors
        error_message = result.get('error_message')
        if error_message:
            logger.error(f"Graph execution error: {error_message}")
            raise HTTPException(status_code=400, detail=error_message)
        
        # Extract results
        constraints = result.get('constraints', {})
        potential_pois = result.get('potential_pois', [])
        
        # Store the result in memory (legacy)
        result['updated_at'] = datetime.utcnow().isoformat()
        trips_store[trip_id] = result
        
        # Persist to Database (Phase 2)
        try:
            async with get_session_context() as session:
                db = DatabaseService(session)
                persistence = StatePersistenceService(session)
                
                # Create trip record
                await db.create_trip(
                    user_id=user_id,
                    trip_id=trip_id,
                    destination=constraints.get('destination', 'Unknown'),
                    constraints=constraints,
                    destination_lat=result.get('destination_coords', {}).get('lat'),
                    destination_lng=result.get('destination_coords', {}).get('lng')
                )
                
                # Save full state (including POIs, hotels, flights)
                await persistence.save_trip_state(trip_id, result)
                logger.info(f"✅ Persisted trip {trip_id} to database")
                
        except Exception as e:
            logger.error(f"Failed to persist trip to database: {e}")
            # Continue even if persistence fails, as we have in-memory fallback
        
        logger.info(f"Trip {trip_id} created successfully with {len(potential_pois)} POIs")
        
        # Format response
        constraints_response = TripConstraintsResponse(**constraints) if constraints else TripConstraintsResponse()
        
        return TripCreateResponse(
            trip_id=trip_id,
            constraints=constraints_response,
            message=f"Found {len(potential_pois)} great places for your trip!",
            pois_found=len(potential_pois)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating trip: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your trip: {str(e)}"
        )


@router.get("/trips/{trip_id}/pois", response_model=TripPOIsResponse, responses={404: {"model": ErrorResponse}})
async def get_trip_pois(trip_id: str, limit: int = 30):
    """
    Get all discovered POIs for a trip.
    
    Returns the list of POIs with their AI scores, rankings, and recommendation reasons.
    
    - **trip_id**: The unique trip identifier
    - **limit**: Maximum number of POIs to return (default 30)
    """
    try:
        # Check if trip exists
        if trip_id not in trips_store:
            logger.warning(f"Trip not found: {trip_id}")
            raise HTTPException(status_code=404, detail="Trip not found")
        
        trip = trips_store[trip_id]
        constraints = trip.get('constraints', {})
        destination = constraints.get('destination')
        destination_coords = trip.get('destination_coords')
        potential_pois = trip.get('potential_pois', [])
        
        # Limit the number of POIs
        pois_to_return = potential_pois[:limit]
        
        # Format POIs for response
        formatted_pois = []
        for poi in pois_to_return:
            try:
                # Extract location
                lat, lng = None, None
                if poi.get('lat') and poi.get('lng'):
                    lat = poi['lat']
                    lng = poi['lng']
                elif poi.get('geometry') and poi['geometry'].get('location'):
                    loc = poi['geometry']['location']
                    lat = loc.get('lat')
                    lng = loc.get('lng')
                
                # Format score breakdown
                score_breakdown_dict = poi.get('score_breakdown', {})
                score_breakdown = POIScoreBreakdown(
                    quality=score_breakdown_dict.get('quality', 50.0),
                    popularity=score_breakdown_dict.get('popularity', 50.0),
                    price_fit=score_breakdown_dict.get('price_fit', 50.0),
                    user_match=score_breakdown_dict.get('user_match'),
                    proximity=score_breakdown_dict.get('proximity')
                )
                
                # Get photo reference
                photo_ref = None
                if poi.get('photos') and len(poi['photos']) > 0:
                    photo_ref = poi['photos'][0].get('photo_reference')
                
                formatted_poi = POIResponse(
                    place_id=poi.get('place_id', ''),
                    name=poi.get('name', 'Unknown'),
                    category=poi.get('types', []),
                    rating=poi.get('rating'),
                    user_ratings_total=poi.get('user_ratings_total'),
                    price_level=poi.get('price_level'),
                    formatted_address=poi.get('formatted_address'),
                    lat=lat,
                    lng=lng,
                    website=poi.get('website'),
                    opening_hours=poi.get('opening_hours'),
                    ai_score=poi.get('ai_score', 50.0),
                    score_breakdown=score_breakdown,
                    why_recommended=poi.get('recommendation_reason', 'Good match for your trip.'),
                    photo_reference=photo_ref
                )
                formatted_pois.append(formatted_poi)
                
            except Exception as e:
                logger.error(f"Error formatting POI {poi.get('name', 'unknown')}: {e}")
                continue
        
        logger.info(f"Returning {len(formatted_pois)} POIs for trip {trip_id}")
        
        return TripPOIsResponse(
            trip_id=trip_id,
            destination=destination,
            destination_coords=destination_coords,
            pois=formatted_pois,
            total_pois=len(formatted_pois)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving POIs for trip {trip_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error retrieving POIs: {str(e)}")


@router.get("/trips/{trip_id}", responses={404: {"model": ErrorResponse}})
async def get_trip(trip_id: str):
    """
    Get full trip details including constraints and POIs.
    
    - **trip_id**: The unique trip identifier
    """
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    trip = trips_store[trip_id]
    
    # Remove large data from response
    response = {
        "trip_id": trip_id,
        "constraints": trip.get('constraints'),
        "destination_coords": trip.get('destination_coords'),
        "pois_count": len(trip.get('potential_pois', [])),
        "current_stage": trip.get('current_stage'),
        "created_at": trip.get('created_at'),
        "updated_at": trip.get('updated_at')
    }
    
    return response


@router.delete("/trips/{trip_id}", responses={404: {"model": ErrorResponse}})
async def delete_trip(trip_id: str):
    """
    Delete a trip.
    
    - **trip_id**: The unique trip identifier
    """
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    del trips_store[trip_id]
    logger.info(f"Deleted trip {trip_id}")
    
    return {"message": "Trip deleted successfully", "trip_id": trip_id}


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check endpoint.
    
    Verifies that the service and its dependencies are operational.
    """
    services_status = {
        "google_maps": "unknown",
        "gemini": "unknown"
    }
    
    # Check Google Maps
    try:
        maps_service = get_google_maps_service()
        test_result = await maps_service.geocode("Paris, France")
        services_status["google_maps"] = "healthy" if test_result else "degraded"
    except Exception as e:
        logger.error(f"Google Maps health check failed: {e}")
        services_status["google_maps"] = "unhealthy"
    
    # Check Gemini
    try:
        gemini_service = get_gemini_service()
        test_response = gemini_service.generate("Hello", max_output_tokens=50)
        services_status["gemini"] = "healthy" if test_response else "degraded"
    except Exception as e:
        logger.error(f"Gemini health check failed: {e}")
        services_status["gemini"] = "unhealthy"
    
    overall_status = "healthy" if all(s == "healthy" for s in services_status.values()) else "degraded"
    
    return HealthCheckResponse(
        status=overall_status,
        phase="1",
        services=services_status
    )






