"""Google Routes API Provider (Phase 2.3 - Week 3).

This module implements the RouteProvider interface using Google Maps Platform APIs.
It provides multi-modal routing, transit schedules, and travel time calculations.

Key Features:
- Multi-modal routing (driving, walking, bicycling, transit)
- Transit schedules and fare information
- Travel time matrix calculation
- Real-time traffic data (driving mode)
- Step-by-step directions
- Polyline encoding for map visualization
"""
import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

import googlemaps
from googlemaps.exceptions import ApiError

from app.config import settings
from app.services.providers.base import RouteProvider, Route
from app.services.cache import get_cache_service
from app.services.cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)


class GoogleRoutesProvider(RouteProvider):
    """Google Maps Platform routing provider.
    
    Features:
    - Multi-modal routing (driving, walking, transit, bicycling)
    - Real-time transit schedules
    - Fare information for public transport
    - Travel time estimates with traffic
    - Step-by-step navigation
    - Alternative routes
    - Caching and cost tracking
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Google Maps client.
        
        Args:
            api_key: Google Maps API key (defaults to settings)
        """
        self.api_key = api_key or settings.google_maps_api_key
        # Increase timeout to 10s and retry window to 60s
        self.client = googlemaps.Client(
            key=self.api_key,
            timeout=10,
            retry_timeout=60
        )
        self.cache = get_cache_service()
        self.cost_tracker = get_cost_tracker()
        
        logger.info("GoogleRoutesProvider initialized with extended timeouts")
    
    async def get_route(
        self,
        origin: dict,
        destination: dict,
        mode: str = "transit",
        departure_time: Optional[str] = None,
        arrival_time: Optional[str] = None,
        options: Optional[dict] = None
    ) -> Optional[Route]:
        """Get a route between two locations.
        
        Args:
            origin: Origin location {"lat": float, "lng": float, "address": str (optional)}
            destination: Destination location
            mode: Travel mode ("transit", "driving", "walking", "bicycling")
            departure_time: Preferred departure time (ISO format or "now")
            arrival_time: Preferred arrival time (ISO format)
            options: Provider-specific options:
                - alternatives: bool (get alternative routes)
                - avoid: List[str] (avoid tolls, highways, ferries)
                - transit_mode: List[str] (bus, subway, train, tram, rail)
                - transit_routing_preference: str (less_walking, fewer_transfers)
                - units: str (metric, imperial)
        
        Returns:
            Route object or None if no route found
        """
        options = options or {}
        
        try:
            # Check cache
            cache_key = self._build_cache_key(origin, destination, mode, departure_time)
            cached = await self.cache.get_route(
                f"{origin['lat']},{origin['lng']}",
                f"{destination['lat']},{destination['lng']}",
                mode
            )
            if cached:
                logger.debug("Cache hit for route")
                return self._parse_cached_route(cached)
            
            # Prepare API request
            origin_str = self._format_location(origin)
            destination_str = self._format_location(destination)
            
            # Build request parameters
            params = {
                'origin': origin_str,
                'destination': destination_str,
                'mode': mode,
                'alternatives': options.get('alternatives', False),
                'units': options.get('units', 'metric')
            }
            
            # Add departure/arrival time
            if departure_time:
                if departure_time == "now":
                    params['departure_time'] = datetime.now()
                else:
                    params['departure_time'] = datetime.fromisoformat(departure_time)
            elif arrival_time:
                params['arrival_time'] = datetime.fromisoformat(arrival_time)
            
            # Transit-specific options
            if mode == 'transit':
                if 'transit_mode' in options:
                    params['transit_mode'] = options['transit_mode']
                if 'transit_routing_preference' in options:
                    params['transit_routing_preference'] = options['transit_routing_preference']
            
            # Driving-specific options
            if mode == 'driving':
                if 'avoid' in options:
                    params['avoid'] = options['avoid']
                # Enable traffic model for better ETA
                if 'departure_time' in params:
                    params['traffic_model'] = 'best_guess'
            
            logger.info(f"Getting route: {origin_str} → {destination_str} ({mode})")
            
            # Make API call in executor (sync → async) with retries
            loop = asyncio.get_event_loop()
            directions_result = None
            
            for attempt in range(3):
                try:
                    directions_result = await loop.run_in_executor(
                        None,
                        lambda: self.client.directions(**params)
                    )
                    break
                except (googlemaps.exceptions.Timeout, googlemaps.exceptions.ApiError) as e:
                    if attempt == 2:
                        logger.error(f"Google Maps API failed after 3 attempts: {e}")
                        raise e
                    logger.warning(f"Google Maps API attempt {attempt + 1} failed: {e}. Retrying...")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            if not directions_result:
                logger.warning("No route found")
                return None
            
            # Parse first route (or best alternative)
            route = self._parse_route(directions_result[0], origin, destination, mode)
            
            if route:
                # Cache result
                await self.cache.set_route(
                    f"{origin['lat']},{origin['lng']}",
                    f"{destination['lat']},{destination['lng']}",
                    mode,
                    route.__dict__
                )
                
                # Track cost
                await self.cost_tracker.track_call(
                    trip_id=None,
                    user_id="system",
                    service="google_maps",
                    endpoint="directions",
                    count=1
                )
            
            return route
            
        except ApiError as e:
            logger.error(f"Google Maps API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting route: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_travel_time_matrix(
        self,
        origins: List[dict],
        destinations: List[dict],
        mode: str = "transit"
    ) -> Optional[List[List[int]]]:
        """Get a matrix of travel times between multiple locations.
        
        Args:
            origins: List of origin locations [{"lat": float, "lng": float}, ...]
            destinations: List of destination locations
            mode: Travel mode
        
        Returns:
            NxM matrix where matrix[i][j] is travel time in seconds
            from origins[i] to destinations[j], or None on error
        """
        try:
            # Prepare locations
            origins_tuples = [(loc['lat'], loc['lng']) for loc in origins]
            destinations_tuples = [(loc['lat'], loc['lng']) for loc in destinations]
            
            logger.info(f"Getting travel time matrix: {len(origins)} × {len(destinations)} ({mode})")
            
            # Make API call with retries
            loop = asyncio.get_event_loop()
            result = None
            
            for attempt in range(3):
                try:
                    result = await loop.run_in_executor(
                        None,
                        lambda: self.client.distance_matrix(
                            origins=origins_tuples,
                            destinations=destinations_tuples,
                            mode=mode
                        )
                    )
                    break
                except (googlemaps.exceptions.Timeout, googlemaps.exceptions.ApiError) as e:
                    if attempt == 2:
                        logger.error(f"Google Maps Matrix API failed after 3 attempts: {e}")
                        raise e
                    logger.warning(f"Google Maps Matrix API attempt {attempt + 1} failed: {e}. Retrying...")
                    await asyncio.sleep(2 ** attempt)
            
            if not result or result['status'] != 'OK':
                logger.error(f"Distance matrix failed: {result.get('status') if result else 'No result'}")
                return None
            
            # Parse into simple matrix
            n = len(origins)
            m = len(destinations)
            time_matrix = [[0] * m for _ in range(n)]
            
            for i, row in enumerate(result['rows']):
                for j, element in enumerate(row['elements']):
                    if element['status'] == 'OK':
                        time_matrix[i][j] = element['duration']['value']
                    else:
                        # No route found, use penalty
                        logger.warning(f"No route from origin {i} to destination {j}")
                        time_matrix[i][j] = 3600  # 1 hour penalty
            
            # Track cost (per 100 elements)
            num_elements = n * m
            await self.cost_tracker.track_call(
                trip_id=None,
                user_id="system",
                service="google_maps",
                endpoint="distance_matrix",
                count=num_elements
            )
            
            logger.info(f"Successfully retrieved {n}×{m} travel time matrix")
            return time_matrix
            
        except Exception as e:
            logger.error(f"Error getting travel time matrix: {e}")
            return None
    
    def _format_location(self, location: dict) -> str:
        """Format location for API request.
        
        Args:
            location: Location dict with lat/lng or address
        
        Returns:
            Formatted location string
        """
        if 'address' in location and location['address']:
            return location['address']
        return f"{location['lat']},{location['lng']}"
    
    def _build_cache_key(self, origin: dict, destination: dict, mode: str, departure_time: Optional[str]) -> str:
        """Build cache key for route."""
        origin_str = f"{origin['lat']},{origin['lng']}"
        dest_str = f"{destination['lat']},{destination['lng']}"
        time_str = departure_time or "any"
        return f"route:{origin_str}:{dest_str}:{mode}:{time_str}"
    
    def _parse_route(self, route_data: dict, origin: dict, destination: dict, mode: str) -> Optional[Route]:
        """Parse Google Directions API response into Route object.
        
        Args:
            route_data: Single route from directions API
            origin: Origin location dict
            destination: Destination location dict
            mode: Travel mode
        
        Returns:
            Route object or None
        """
        try:
            leg = route_data['legs'][0]  # Single leg route
            
            # Extract basic info
            duration_seconds = leg['duration']['value']
            distance_meters = leg['distance']['value']
            
            # Extract polyline (for map visualization)
            polyline = route_data.get('overview_polyline', {}).get('points')
            
            # Parse steps (transit legs, walking segments, etc.)
            steps = []
            fare_info = None
            
            for step in leg.get('steps', []):
                step_data = {
                    'travel_mode': step.get('travel_mode', mode).lower(),
                    'duration': step['duration']['value'],
                    'distance': step['distance']['value'],
                    'instructions': step.get('html_instructions', ''),
                    'start_location': step['start_location'],
                    'end_location': step['end_location']
                }
                
                # Transit-specific data
                if 'transit_details' in step:
                    transit = step['transit_details']
                    step_data['transit'] = {
                        'line': {
                            'name': transit['line'].get('name'),
                            'short_name': transit['line'].get('short_name'),
                            'vehicle': transit['line']['vehicle']['name'],
                            'color': transit['line'].get('color'),
                            'icon': transit['line'].get('icon')
                        },
                        'departure_stop': transit['departure_stop']['name'],
                        'arrival_stop': transit['arrival_stop']['name'],
                        'departure_time': transit['departure_time']['text'],
                        'arrival_time': transit['arrival_time']['text'],
                        'num_stops': transit.get('num_stops', 0),
                        'headsign': transit.get('headsign')
                    }
                
                steps.append(step_data)
            
            # Extract fare (if available for transit)
            if 'fare' in leg:
                fare_info = {
                    'amount': float(leg['fare']['value']),
                    'currency': leg['fare']['currency']
                }
            
            # Extract departure/arrival times (if available)
            departure_time = None
            arrival_time = None
            if 'departure_time' in leg:
                departure_time = leg['departure_time']['text']
            if 'arrival_time' in leg:
                arrival_time = leg['arrival_time']['text']
            
            # Create Route object
            route = Route(
                provider="google_maps",
                origin=origin,
                destination=destination,
                mode=mode,
                duration_seconds=duration_seconds,
                distance_meters=distance_meters,
                fare=fare_info,
                steps=steps,
                polyline=polyline,
                departure_time=departure_time,
                arrival_time=arrival_time,
                raw_data=route_data
            )
            
            return route
            
        except Exception as e:
            logger.error(f"Error parsing route: {e}")
            return None
    
    def _parse_cached_route(self, cached_data: dict) -> Optional[Route]:
        """Parse cached route data back into Route object."""
        try:
            return Route(**cached_data)
        except Exception as e:
            logger.error(f"Error parsing cached route: {e}")
            return None


# Singleton instance
_google_routes_provider: Optional[GoogleRoutesProvider] = None


def get_google_routes_provider() -> GoogleRoutesProvider:
    """Get or create the global GoogleRoutesProvider instance."""
    global _google_routes_provider
    if _google_routes_provider is None:
        _google_routes_provider = GoogleRoutesProvider()
    return _google_routes_provider

