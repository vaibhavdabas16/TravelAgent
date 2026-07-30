"""Google Maps Platform API client service.

Provides geocoding, place search, and place details functionality using the
google-maps-services-python library.

Phase 2.4: Added caching and cost tracking.
"""
import logging
import asyncio
from typing import Optional
import googlemaps
from googlemaps.exceptions import ApiError

from app.config import settings
from app.services.cache import get_cache_service
from app.services.cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Client for Google Maps Platform APIs with caching and cost tracking."""
    
    def __init__(self):
        """Initialize the Google Maps client with API key from settings."""
        self.client = googlemaps.Client(key=settings.google_maps_api_key)
        self.cache = get_cache_service()
        self.cost_tracker = get_cost_tracker()
        logger.info("GoogleMapsService initialized")
    
    async def geocode(
        self,
        address: str,
        user_id: Optional[str] = None,
        trip_id: Optional[str] = None
    ) -> Optional[dict]:
        """
        Geocode a human-readable address into latitude and longitude.
        
        Uses caching (7-day TTL) and tracks costs.
        
        Args:
            address: The address or place name to geocode (e.g., "Eiffel Tower, Paris")
            user_id: User ID for cost tracking (optional)
            trip_id: Trip ID for cost tracking (optional)
            
        Returns:
            Dictionary with 'lat', 'lng', and 'formatted_address', or None if not found
            
        Example:
            >>> service = GoogleMapsService()
            >>> result = await service.geocode("Tokyo, Japan")
            >>> print(result)
            {'lat': 35.6762, 'lng': 139.6503, 'formatted_address': 'Tokyo, Japan'}
        """
        # Check cache first
        cached = await self.cache.get_geocoding(address)
        if cached:
            logger.debug(f"Cache hit for geocode: {address}")
            return cached
        
        try:
            # Call sync Google Maps API in executor to avoid blocking
            loop = asyncio.get_event_loop()
            geocode_result = await loop.run_in_executor(
                None,
                self.client.geocode,
                address
            )
            
            if geocode_result:
                location = geocode_result[0]['geometry']['location']
                formatted_address = geocode_result[0]['formatted_address']
                
                result = {
                    "lat": location['lat'],
                    "lng": location['lng'],
                    "formatted_address": formatted_address
                }
                
                # Cache result
                await self.cache.set_geocoding(address, result)
                
                # Track cost
                if user_id:
                    await self.cost_tracker.track_call(
                        trip_id, user_id, "google_maps", "geocoding"
                    )
                
                logger.info(f"Successfully geocoded '{address}' to {result}")
                return result
            else:
                logger.warning(f"No geocoding results found for: {address}")
                return None
                
        except ApiError as e:
            logger.error(f"Google Maps API error during geocoding: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during geocoding: {e}")
            return None
    
    def find_place(self, query: str, fields: Optional[list] = None) -> Optional[list]:
        """
        Find a specific place by its name or address using text search.
        
        Args:
            query: The search query (e.g., "Delfina Restaurant in San Francisco")
            fields: List of fields to return. Defaults to essential fields.
            
        Returns:
            List of place candidates with their details, or None if not found
        """
        if fields is None:
            fields = [
                'place_id', 'name', 'formatted_address', 'geometry',
                'rating', 'user_ratings_total', 'types', 'price_level'
            ]
        
        try:
            places_result = self.client.find_place(
                input=query,
                input_type='textquery',
                fields=fields
            )
            
            if places_result and 'candidates' in places_result and places_result['candidates']:
                logger.info(f"Found {len(places_result['candidates'])} places for query: {query}")
                return places_result['candidates']
            else:
                logger.warning(f"No places found for query: {query}")
                return None
                
        except ApiError as e:
            logger.error(f"Google Maps API error during find_place: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during find_place: {e}")
            return None
    
    def nearby_search(
        self, 
        location: dict, 
        radius: int, 
        place_type: Optional[str] = None,
        keyword: Optional[str] = None
    ) -> list:
        """
        Find places of a specific type near a given location.
        
        Args:
            location: Dict with 'lat' and 'lng' keys
            radius: Search radius in meters (max 50000)
            place_type: Type of place (e.g., 'restaurant', 'museum', 'cafe')
            keyword: Additional keyword to filter results
            
        Returns:
            List of nearby places with their details
            
        Example:
            >>> location = {"lat": 48.8584, "lng": 2.2945}
            >>> places = service.nearby_search(location, 1000, 'cafe')
        """
        try:
            # Build search parameters
            search_params = {
                'location': (location['lat'], location['lng']),
                'radius': radius
            }
            
            if place_type:
                search_params['type'] = place_type
            if keyword:
                search_params['keyword'] = keyword
            
            nearby_result = self.client.places_nearby(**search_params)
            
            places = nearby_result.get('results', [])
            logger.info(
                f"Found {len(places)} {place_type or 'places'} within {radius}m "
                f"of ({location['lat']}, {location['lng']})"
            )
            return places
            
        except ApiError as e:
            logger.error(f"Google Maps API error during nearby_search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during nearby_search: {e}")
            return []
    
    def text_search(
        self, 
        query: str, 
        location: Optional[dict] = None,
        radius: Optional[int] = None
    ) -> list:
        """
        Search for places using a text query.
        
        Args:
            query: Text query (e.g., "hotels in Manali")
            location: Optional bias location {'lat': float, 'lng': float}
            radius: Optional bias radius in meters
            
        Returns:
            List of places
        """
        try:
            # Build search parameters
            search_params = {'query': query}
            
            if location and radius:
                search_params['location'] = (location['lat'], location['lng'])
                search_params['radius'] = radius
            
            result = self.client.places(**search_params)
            
            places = result.get('results', [])
            logger.info(f"Found {len(places)} places for query '{query}'")
            return places
            
        except ApiError as e:
            logger.error(f"Google Maps API error during text_search: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during text_search: {e}")
            return []

    def place_details(self, place_id: str, fields: Optional[list] = None) -> Optional[dict]:
        """
        Retrieve detailed information for a specific place.
        
        Args:
            place_id: The unique Google Places identifier
            fields: List of fields to return. Defaults to comprehensive fields.
            
        Returns:
            Dictionary of detailed place information, or None if not found
            
        Example:
            >>> details = service.place_details('ChIJN1t_tDeuEmsRUsoyG83frY4')
            >>> print(details['name'], details['rating'])
        """
        if fields is None:
            fields = [
                'name', 'formatted_address', 'geometry', 'opening_hours',
                'website', 'rating', 'user_ratings_total', 'reviews',
                'photo', 'price_level', 'formatted_phone_number', 'business_status'
            ]
        
        try:
            details_result = self.client.place(
                place_id=place_id,
                fields=fields
            )
            
            if 'result' in details_result:
                logger.info(f"Retrieved details for place_id: {place_id}")
                return details_result['result']
            else:
                logger.warning(f"No details found for place_id: {place_id}")
                return None
                
        except ApiError as e:
            logger.error(f"Google Maps API error during place_details: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during place_details: {e}")
            return None
    
    def get_distance_matrix(
        self,
        origins: list[dict],
        destinations: list[dict],
        mode: str = "driving"
    ) -> Optional[dict]:
        """
        Get travel distance and time between multiple origins and destinations.
        
        Args:
            origins: List of location dicts with 'lat' and 'lng'
            destinations: List of location dicts with 'lat' and 'lng'
            mode: Travel mode ('driving', 'walking', 'bicycling', 'transit')
            
        Returns:
            Distance matrix with durations and distances, or None on error
        """
        try:
            # Convert to tuples format required by the API
            origins_tuples = [(loc['lat'], loc['lng']) for loc in origins]
            destinations_tuples = [(loc['lat'], loc['lng']) for loc in destinations]
            
            result = self.client.distance_matrix(
                origins=origins_tuples,
                destinations=destinations_tuples,
                mode=mode
            )
            
            logger.info(f"Retrieved distance matrix for {len(origins)} origins and {len(destinations)} destinations")
            return result
            
        except ApiError as e:
            logger.error(f"Google Maps API error during distance_matrix: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during distance_matrix: {e}")
            return None
    
    def calculate_travel_time_matrix(
        self,
        pois: list[dict],
        mode: str = "walking"
    ) -> Optional[list[list[int]]]:
        """
        Calculate a travel time matrix for a list of POIs.
        
        Args:
            pois: List of POI dicts with 'location' dict containing 'lat' and 'lng'
            mode: Travel mode ('driving', 'walking', 'bicycling', 'transit')
            
        Returns:
            NxN matrix where matrix[i][j] is travel time in seconds from POI i to POI j,
            or None on error
            
        Example:
            >>> pois = [
            ...     {'name': 'Louvre', 'location': {'lat': 48.8606, 'lng': 2.3376}},
            ...     {'name': 'Eiffel Tower', 'location': {'lat': 48.8584, 'lng': 2.2945}}
            ... ]
            >>> matrix = service.calculate_travel_time_matrix(pois)
            >>> # matrix[0][1] is travel time from Louvre to Eiffel Tower in seconds
        """
        try:
            # Extract locations
            locations = [poi['location'] for poi in pois]
            
            # Get distance matrix from Google Maps
            result = self.get_distance_matrix(
                origins=locations,
                destinations=locations,
                mode=mode
            )
            
            if not result or result['status'] != 'OK':
                logger.error(f"Distance matrix request failed: {result.get('status') if result else 'No result'}")
                return None
            
            # Extract travel times into a simple matrix (in seconds)
            n = len(pois)
            time_matrix = [[0] * n for _ in range(n)]
            
            for i, row in enumerate(result['rows']):
                for j, element in enumerate(row['elements']):
                    if element['status'] == 'OK':
                        # Duration in seconds
                        time_matrix[i][j] = element['duration']['value']
                    else:
                        # If route not found, use a large penalty
                        logger.warning(f"No route from POI {i} to POI {j}, using penalty")
                        time_matrix[i][j] = 3600  # 1 hour penalty
            
            return time_matrix
            
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing distance matrix response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error calculating travel time matrix: {e}")
            return None


# Global service instance
_google_maps_service: Optional[GoogleMapsService] = None


def get_google_maps_service() -> GoogleMapsService:
    """Get or create the global GoogleMapsService instance."""
    global _google_maps_service
    if _google_maps_service is None:
        _google_maps_service = GoogleMapsService()
    return _google_maps_service

