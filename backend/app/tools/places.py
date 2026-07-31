"""Places discovery tools for LangGraph agents."""
import logging
from langchain_core.tools import tool

from app.services.google_maps import get_google_maps_service

logger = logging.getLogger(__name__)


@tool
async def discover_places(location: str, place_type: str, radius_meters: int = 5000) -> list:
    """
    Discovers points of interest near a location.
    
    Use this tool to find places like restaurants, museums, parks, etc.
    in a given area. The tool will geocode the location first, then search nearby.
    
    Args:
        location: Destination name (e.g., "Barcelona, Spain", "Central Paris")
        place_type: Type of place - examples:
            - "restaurant" (dining)
            - "museum" (museums)
            - "tourist_attraction" (major attractions)
            - "park" (parks and outdoors)
            - "cafe" (cafes and coffee shops)
            - "shopping_mall" (shopping)
            - "night_club" (nightlife)
            - "spa" (wellness)
        radius_meters: Search radius in meters (default 5000m = 5km, max 50000)
    
    Returns:
        List of places with details including:
        - place_id: Unique identifier
        - name: Place name
        - rating: Google rating (0-5)
        - user_ratings_total: Number of reviews
        - price_level: Price indicator (0-4)
        - types: Categories
        - geometry: Location data with lat/lng
        - opening_hours: Operating hours if available
        - reviews: Sample reviews (top 3)
    
    Example:
        discover_places("Rome, Italy", "museum", 3000)
        → Returns list of museums within 3km of Rome city center
    """
    try:
        service = get_google_maps_service()
        
        # First, geocode the location (async method)
        coords = await service.geocode(location)
        if not coords:
            logger.warning(f"Could not geocode location for discovery: {location}")
            return []
        
        # Search for nearby places using text search for better relevance
        # "top {place_type} in {location}" usually yields better results than nearby_search from a centroid
        query = f"top {place_type} in {location}"
        
        places = service.text_search(
            query=query,
            location={"lat": coords['lat'], "lng": coords['lng']},
            radius=radius_meters
        )
        
        if not places:
            logger.info(f"No {place_type} places found near {location}")
            return []
        
        # Enrich top places with detailed information
        enriched_places = []
        for place in places[:15]:  # Limit to top 15 to save API quota
            place_id = place.get('place_id')
            if not place_id:
                continue
            
            # Get detailed information
            details = service.place_details(place_id)
            if details:
                # Combine basic + detailed info
                enriched = {
                    "place_id": place_id,
                    "name": place.get('name'),
                    "rating": place.get('rating'),
                    "user_ratings_total": place.get('user_ratings_total', 0),
                    "price_level": place.get('price_level'),
                    "types": place.get('types', []),
                    "geometry": place.get('geometry'),
                    "formatted_address": details.get('formatted_address'),
                    "opening_hours": details.get('opening_hours'),
                    "website": details.get('website'),
                    "reviews": details.get('reviews', [])[:3],  # Top 3 reviews
                    "photos": details.get('photos', [])[:1] if details.get('photos') else []
                }
                
                # Extract lat/lng for easier access
                if enriched.get('geometry') and enriched['geometry'].get('location'):
                    loc = enriched['geometry']['location']
                    enriched['lat'] = loc.get('lat')
                    enriched['lng'] = loc.get('lng')
                
                enriched_places.append(enriched)
            else:
                # Fallback to basic info if details fail
                basic = {
                    "place_id": place_id,
                    "name": place.get('name'),
                    "rating": place.get('rating'),
                    "user_ratings_total": place.get('user_ratings_total', 0),
                    "price_level": place.get('price_level'),
                    "types": place.get('types', []),
                    "geometry": place.get('geometry')
                }
                enriched_places.append(basic)
        
        logger.info(f"Discovered {len(enriched_places)} {place_type} places near {location}")
        return enriched_places
        
    except Exception as e:
        logger.error(f"Error discovering places: {e}")
        return []


@tool
def get_place_details(place_id: str) -> dict:
    """
    Gets detailed information for a specific place.
    
    Use this tool when you need comprehensive information about a place
    you already have a place_id for.
    
    Args:
        place_id: The unique Google Places identifier
    
    Returns:
        Dictionary with comprehensive place details including:
        - name, address, location
        - rating, reviews
        - opening hours
        - photos, website
        - price level
    """
    try:
        service = get_google_maps_service()
        details = service.place_details(place_id)
        
        if details:
            logger.info(f"Retrieved details for place_id: {place_id}")
            return details
        else:
            error = {"error": f"Could not find details for place_id: {place_id}"}
            logger.warning(f"Place details not found: {place_id}")
            return error
            
    except Exception as e:
        error = {"error": f"Error getting place details: {str(e)}"}
        logger.error(f"Place details error for '{place_id}': {e}")
        return error






