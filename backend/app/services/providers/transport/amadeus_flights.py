"""Amadeus Flight Search API Provider (Phase 2.3).

This module implements the FlightProvider interface using the Amadeus Self-Service API.
It uses the Flight Offers Search API for one-way, round-trip, and multi-city flights.

Key Features:
- Direct flight search (no two-step workflow like hotels)
- One-way and round-trip support
- Multi-city itineraries
- Cabin class filtering
- Price sorting
- CO2 emissions data
"""
import logging
from typing import List, Optional
from datetime import date, datetime

from amadeus import Client, ResponseError

from app.config import settings
from app.services.providers.base import FlightProvider, Flight
from app.services.cache import get_cache_service
from app.services.cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)


class AmadeusFlightProvider(FlightProvider):
    """Amadeus Flight Offers Search API provider.
    
    Features:
    - One-way and round-trip flights
    - Multi-city support
    - Cabin class filtering (economy, premium, business, first)
    - Direct flights and connections
    - CO2 emissions data
    - Real-time pricing
    - Caching and cost tracking
    """
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """Initialize the Amadeus client.
        
        Args:
            client_id: Amadeus API key (defaults to settings)
            client_secret: Amadeus API secret (defaults to settings)
        """
        self.client_id = client_id or settings.amadeus_api_key
        self.client_secret = client_secret or settings.amadeus_api_secret
        
        # Determine environment from base URL
        hostname = 'test' if 'test.api.amadeus.com' in settings.amadeus_base_url else 'production'
        
        # Initialize SDK client (handles OAuth2 automatically)
        self.client = Client(
            client_id=self.client_id,
            client_secret=self.client_secret,
            hostname=hostname,
            log_level='warn'
        )
        
        self.cache = get_cache_service()
        self.cost_tracker = get_cost_tracker()
        
        logger.info(f"AmadeusFlightProvider initialized (environment: {hostname})")
    
    async def search(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: Optional[date] = None,
        num_passengers: int = 1,
        cabin_class: str = "economy",
        filters: Optional[dict] = None
    ) -> List[Flight]:
        """Search for flights using Amadeus Flight Offers Search API.
        
        Args:
            origin: Origin airport code (e.g., "JFK") or city code (e.g., "NYC")
            destination: Destination airport code or city code
            departure_date: Departure date
            return_date: Return date (None for one-way)
            num_passengers: Number of adult passengers (1-9)
            cabin_class: Preferred cabin class ("economy", "premium_economy", "business", "first")
            filters: Optional filters:
                - max_results: int (default 50, max 250)
                - non_stop: bool (only direct flights)
                - max_price: float
                - currency: str (default "USD")
                - max_stops: int (0, 1, 2)
        
        Returns:
            List of Flight objects sorted by price
        """
        filters = filters or {}
        max_results = min(filters.get('max_results', 50), 250)  # Amadeus max 250
        
        try:
            # Build search parameters
            params = {
                'originLocationCode': origin.upper(),
                'destinationLocationCode': destination.upper(),
                'departureDate': departure_date.isoformat(),
                'adults': str(num_passengers),
                'max': str(max_results),
                'currencyCode': filters.get('currency', 'USD')
            }
            
            # Add return date for round-trip
            if return_date:
                params['returnDate'] = return_date.isoformat()
            
            # Map cabin class to Amadeus values
            cabin_map = {
                'economy': 'ECONOMY',
                'premium_economy': 'PREMIUM_ECONOMY',
                'business': 'BUSINESS',
                'first': 'FIRST'
            }
            params['travelClass'] = cabin_map.get(cabin_class.lower(), 'ECONOMY')
            
            # Apply filters
            if filters.get('non_stop'):
                params['nonStop'] = 'true'
            
            if 'max_price' in filters:
                params['maxPrice'] = str(filters['max_price'])
            
            logger.info(f"Searching flights: {origin} → {destination} on {departure_date}")
            
            # Make API request
            response = self.client.shopping.flight_offers_search.get(**params)
            
            # Parse flights
            flights = []
            for offer_data in response.data:
                flight_list = self._parse_flight_offer(offer_data, filters)
                flights.extend(flight_list)
            
            # Sort by price
            flights.sort(key=lambda f: f.price)
            
            # Track cost
            await self.cost_tracker.track_call(
                trip_id=None,
                user_id="system",
                service="amadeus",
                endpoint="flight_offers_search",
                count=1  # Per search request
            )
            
            logger.info(f"Found {len(flights)} flight offers")
            return flights
            
        except ResponseError as e:
            logger.error(f"Amadeus API error during flight search: {e}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.body}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during flight search: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_flight_offer(self, offer_data: dict, filters: dict) -> List[Flight]:
        """Parse Amadeus API response into Flight objects.
        
        An offer can contain multiple itineraries (outbound + return).
        We create separate Flight objects for each direction.
        
        Args:
            offer_data: Raw offer data from Amadeus API
            filters: Search filters (for max_stops filtering)
        
        Returns:
            List of Flight objects (1 for one-way, 2 for round-trip)
        """
        flights = []
        
        try:
            price_info = offer_data.get('price', {})
            total_price = float(price_info.get('total', 0))
            currency = price_info.get('currency', 'USD')
            offer_id = offer_data.get('id')
            
            # Each itinerary is a direction (outbound or return)
            itineraries = offer_data.get('itineraries', [])
            
            for itinerary_idx, itinerary in enumerate(itineraries):
                segments = itinerary.get('segments', [])
                
                if not segments:
                    continue
                
                # Calculate total stops
                num_stops = len(segments) - 1
                
                # Apply max_stops filter
                if 'max_stops' in filters and num_stops > filters['max_stops']:
                    continue
                
                # Extract layover airports
                layover_airports = []
                if num_stops > 0:
                    for seg in segments[:-1]:  # All except last
                        layover_airports.append(seg['arrival']['iataCode'])
                
                # First segment for origin and departure
                first_seg = segments[0]
                last_seg = segments[-1]
                
                # Parse dates
                departure_dt = first_seg['departure']['at']
                arrival_dt = last_seg['arrival']['at']
                
                # Calculate duration (sum of all segment durations)
                total_duration = itinerary.get('duration', 'PT0H')
                duration_minutes = self._parse_duration(total_duration)
                
                # Get airline (primary carrier)
                airline_code = first_seg.get('carrierCode', first_seg.get('operating', {}).get('carrierCode', 'XX'))
                airline_name = self._get_airline_name(airline_code)
                
                # Flight number (first segment)
                flight_number = f"{airline_code}{first_seg.get('number', '')}"
                
                # Get traveler pricing (split price for multi-traveler bookings)
                traveler_pricings = offer_data.get('travelerPricings', [])
                num_travelers = len(traveler_pricings)
                price_per_traveler = total_price / max(num_travelers, 1)
                
                # For round-trip, split price between outbound and return
                if len(itineraries) > 1:
                    price_per_traveler = price_per_traveler / len(itineraries)
                
                # Get cabin class from first segment
                cabin_class = None
                if traveler_pricings and 'fareDetailsBySegment' in traveler_pricings[0]:
                    fare_details = traveler_pricings[0]['fareDetailsBySegment']
                    if fare_details:
                        cabin_class = fare_details[0].get('cabin', '').lower()
                
                # Get baggage allowance
                baggage = None
                if traveler_pricings and 'fareDetailsBySegment' in traveler_pricings[0]:
                    fare_details = traveler_pricings[0]['fareDetailsBySegment']
                    if fare_details and 'includedCheckedBags' in fare_details[0]:
                        bags = fare_details[0]['includedCheckedBags']
                        if isinstance(bags, dict):
                            if 'quantity' in bags:
                                baggage = f"{bags['quantity']} bag(s)"
                            elif 'weight' in bags:
                                baggage = f"{bags['weight']} {bags.get('weightUnit', 'kg')}"
                
                # CO2 emissions (if available)
                co2_emissions = None
                if segments[0].get('co2Emissions'):
                    for seg in segments:
                        emissions = seg.get('co2Emissions', [])
                        if emissions:
                            co2_emissions = (co2_emissions or 0) + emissions[0].get('weight', 0)
                
                # Create Flight object
                flight = Flight(
                    provider="amadeus",
                    provider_id=offer_id,
                    origin=first_seg['departure']['iataCode'],
                    destination=last_seg['arrival']['iataCode'],
                    departure_datetime=departure_dt,
                    arrival_datetime=arrival_dt,
                    duration_minutes=duration_minutes,
                    price=round(price_per_traveler, 2),
                    currency=currency,
                    airline=airline_name,
                    flight_number=flight_number,
                    stops=num_stops,
                    layover_airports=layover_airports,
                    cabin_class=cabin_class,
                    baggage_allowance=baggage,
                    co2_emissions_kg=co2_emissions,
                    offer_id=offer_id,
                    raw_data=offer_data
                )
                
                flights.append(flight)
            
            return flights
            
        except Exception as e:
            logger.error(f"Error parsing flight offer: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parse ISO 8601 duration to minutes.
        
        Example: "PT2H30M" → 150 minutes
        
        Args:
            duration_str: ISO 8601 duration string
        
        Returns:
            Total minutes
        """
        import re
        
        # Remove PT prefix
        duration_str = duration_str.replace('PT', '')
        
        hours = 0
        minutes = 0
        
        # Extract hours
        hour_match = re.search(r'(\d+)H', duration_str)
        if hour_match:
            hours = int(hour_match.group(1))
        
        # Extract minutes
        min_match = re.search(r'(\d+)M', duration_str)
        if min_match:
            minutes = int(min_match.group(1))
        
        return hours * 60 + minutes
    
    def _get_airline_name(self, airline_code: str) -> str:
        """Get airline name from IATA code.
        
        Args:
            airline_code: IATA airline code (e.g., "AA")
        
        Returns:
            Airline name or code if unknown
        """
        # Common airlines (subset for testing)
        airlines = {
            'AA': 'American Airlines',
            'UA': 'United Airlines',
            'DL': 'Delta Air Lines',
            'BA': 'British Airways',
            'AF': 'Air France',
            'LH': 'Lufthansa',
            'EK': 'Emirates',
            'QR': 'Qatar Airways',
            'SQ': 'Singapore Airlines',
            'JL': 'Japan Airlines',
            'NH': 'ANA',
            'CX': 'Cathay Pacific',
            'KL': 'KLM',
            'IB': 'Iberia',
            'AY': 'Finnair',
            'SK': 'SAS',
            'LX': 'Swiss',
            'OS': 'Austrian',
            'TP': 'TAP Portugal',
            'AZ': 'ITA Airways'
        }
        
        return airlines.get(airline_code, airline_code)
    
    async def get_details(self, offer_id: str) -> Optional[Flight]:
        """Get detailed information for a specific flight offer.
        
        This is used for price confirmation before booking.
        
        Args:
            offer_id: Flight offer ID from search results
        
        Returns:
            Flight object with confirmed pricing or None if not available
        """
        try:
            # Flight Offer Price endpoint for confirmation
            response = self.client.shopping.flight_offers.pricing.post(
                {
                    "data": {
                        "type": "flight-offers-pricing",
                        "flightOffers": [{"id": offer_id}]
                    }
                }
            )
            
            if response.data and 'flightOffers' in response.data:
                offer_data = response.data['flightOffers'][0]
                flights = self._parse_flight_offer(offer_data, {})
                if flights:
                    return flights[0]
            
            return None
            
        except ResponseError as e:
            logger.error(f"Error getting flight details: {e}")
            return None


# Singleton instance
_amadeus_flight_provider: Optional[AmadeusFlightProvider] = None


def get_amadeus_flight_provider() -> AmadeusFlightProvider:
    """Get or create the global AmadeusFlightProvider instance."""
    global _amadeus_flight_provider
    if _amadeus_flight_provider is None:
        _amadeus_flight_provider = AmadeusFlightProvider()
    return _amadeus_flight_provider

