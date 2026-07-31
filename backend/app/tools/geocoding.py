"""Geocoding tool for LangGraph agents."""
import logging
from langchain_core.tools import tool

from app.services.google_maps import get_google_maps_service

logger = logging.getLogger(__name__)


@tool
async def geocode_location(location: str) -> dict:
    """
    Converts a location name or address to geographic coordinates.
    
    Use this tool when you need to find the latitude and longitude
    of a city, landmark, or address.
    
    Args:
        location: City name, address, or landmark (e.g., "Paris, France", "Eiffel Tower")
    
    Returns:
        Dictionary with 'lat', 'lng', and 'formatted_address', or error dict
    
    Examples:
        - "Tokyo, Japan" → {"lat": 35.6762, "lng": 139.6503, "formatted_address": "Tokyo, Japan"}
        - "Louvre Museum" → {"lat": 48.8606, "lng": 2.3376, "formatted_address": "..."}
    """
    try:
        service = get_google_maps_service()
        
        # Call async service directly
        result = await service.geocode(location)
        
        if result:
            logger.info(f"Successfully geocoded: {location}")
            return result
        else:
            error = {"error": f"Could not geocode location: {location}"}
            logger.warning(f"Geocoding failed: {location}")
            return error
            
    except Exception as e:
        error = {"error": f"Geocoding error: {str(e)}"}
        logger.error(f"Geocoding exception for '{location}': {e}")
        return error
            
    except Exception as e:
        error = {"error": f"Geocoding error: {str(e)}"}
        logger.error(f"Geocoding exception for '{location}': {e}")
        return error






