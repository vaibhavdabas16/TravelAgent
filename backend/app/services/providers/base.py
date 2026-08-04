"""Base classes for data providers (Phase 2.3).

This module defines abstract base classes for accommodation, flight, and transport providers.
The swappable provider pattern allows easy switching between different data sources
(e.g., Amadeus API, SerpAPI, scrapers) without changing application code.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from datetime import date


# ==================== Data Models ====================

@dataclass
class Hotel:
    """Standardized hotel data model.
    
    All accommodation providers must transform their responses to this format.
    """
    provider: str  # "amadeus", "serpapi", etc.
    provider_id: str  # Unique ID in the provider's system
    name: str
    latitude: float
    longitude: float
    price_per_night: float  # Average per night
    total_price: float  # Total for entire stay
    currency: str
    rating: Optional[float] = None  # 0-5 scale
    review_count: Optional[int] = None
    photo_url: Optional[str] = None
    photos: List[dict] = None  # List of photo objects from provider
    amenities: List[str] = None
    cancellation_policy: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    
    # Offer-specific fields
    offer_id: Optional[str] = None  # For booking
    check_in: Optional[str] = None  # YYYY-MM-DD
    check_out: Optional[str] = None  # YYYY-MM-DD
    
    # Computed fields (set by application)
    avg_commute_time_minutes: Optional[int] = None
    ai_score: Optional[float] = None
    
    # Raw data for debugging
    raw_data: Optional[dict] = None
    
    def __post_init__(self):
        """Ensure amenities is a list."""
        if self.amenities is None:
            self.amenities = []


@dataclass
class Flight:
    """Standardized flight data model."""
    provider: str
    provider_id: str
    origin: str  # Airport code
    destination: str  # Airport code
    departure_datetime: str  # ISO format
    arrival_datetime: str  # ISO format
    duration_minutes: int
    price: float
    currency: str
    airline: str
    flight_number: Optional[str] = None
    stops: int = 0
    layover_airports: List[str] = None
    cabin_class: Optional[str] = None  # "economy", "business", "first"
    baggage_allowance: Optional[str] = None
    co2_emissions_kg: Optional[float] = None
    
    # Booking fields
    offer_id: Optional[str] = None
    
    # Computed fields
    ai_score: Optional[float] = None
    
    raw_data: Optional[dict] = None
    
    def __post_init__(self):
        """Ensure layover_airports is a list."""
        if self.layover_airports is None:
            self.layover_airports = []


@dataclass
class Route:
    """Standardized multi-modal route data model."""
    provider: str
    origin: dict  # {"lat": float, "lng": float, "address": str}
    destination: dict
    mode: str  # "driving", "walking", "transit", "bicycling"
    duration_seconds: int
    distance_meters: int
    fare: Optional[dict] = None  # {"amount": float, "currency": str}
    steps: List[dict] = None  # Transit legs
    polyline: Optional[str] = None  # Encoded polyline for map display
    departure_time: Optional[str] = None  # ISO format
    arrival_time: Optional[str] = None
    
    raw_data: Optional[dict] = None
    
    def __post_init__(self):
        """Ensure steps is a list."""
        if self.steps is None:
            self.steps = []


# ==================== Abstract Providers ====================

class AccommodationProvider(ABC):
    """Abstract base class for accommodation data sources."""
    
    @abstractmethod
    async def search(
        self,
        destination: str,
        checkin_date: date,
        checkout_date: date,
        num_guests: int,
        filters: Optional[dict] = None
    ) -> List[Hotel]:
        """Search for hotels.
        
        Args:
            destination: City name, IATA code, or lat/lng
            checkin_date: Check-in date
            checkout_date: Check-out date
            num_guests: Number of adult guests
            filters: Optional filters (rating, price_range, amenities, etc.)
        
        Returns:
            List of Hotel objects sorted by relevance/price
        """
        pass
    
    @abstractmethod
    async def get_details(self, provider_id: str, offer_id: Optional[str] = None) -> Optional[Hotel]:
        """Get detailed information for a specific hotel/offer.
        
        Args:
            provider_id: Hotel ID in the provider's system
            offer_id: Optional offer ID for price confirmation
        
        Returns:
            Hotel object with full details or None if not found
        """
        pass


class FlightProvider(ABC):
    """Abstract base class for flight data sources."""
    
    @abstractmethod
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
        """Search for flights.
        
        Args:
            origin: Origin airport code or city
            destination: Destination airport code or city
            departure_date: Departure date
            return_date: Return date (None for one-way)
            num_passengers: Number of passengers
            cabin_class: Preferred cabin class
            filters: Optional filters (airlines, stops, etc.)
        
        Returns:
            List of Flight objects sorted by price/convenience
        """
        pass
    
    @abstractmethod
    async def get_details(self, offer_id: str) -> Optional[Flight]:
        """Get detailed information for a specific flight offer.
        
        Args:
            offer_id: Flight offer ID in the provider's system
        
        Returns:
            Flight object with full details or None if not found
        """
        pass


class RouteProvider(ABC):
    """Abstract base class for route planning data sources."""
    
    @abstractmethod
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
            origin: Origin location {"lat": float, "lng": float}
            destination: Destination location
            mode: Travel mode ("transit", "driving", "walking", "bicycling")
            departure_time: Preferred departure time (ISO format)
            arrival_time: Preferred arrival time (ISO format)
            options: Provider-specific options
        
        Returns:
            Route object or None if no route found
        """
        pass
    
    @abstractmethod
    async def get_travel_time_matrix(
        self,
        origins: List[dict],
        destinations: List[dict],
        mode: str = "transit"
    ) -> Optional[List[List[int]]]:
        """Get a matrix of travel times between multiple locations.
        
        Args:
            origins: List of origin locations
            destinations: List of destination locations
            mode: Travel mode
        
        Returns:
            NxM matrix where matrix[i][j] is travel time in seconds
            from origins[i] to destinations[j], or None on error
        """
        pass








