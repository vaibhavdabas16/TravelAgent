"""Data providers package (Phase 2.3).

This package contains swappable providers for accommodation, flights, and transport.
"""
from app.services.providers.base import (
    Hotel,
    Flight,
    Route,
    AccommodationProvider,
    FlightProvider,
    RouteProvider
)
from app.services.providers.accommodation import AmadeusHotelProvider
from app.services.providers.transport import AmadeusFlightProvider, GoogleRoutesProvider

__all__ = [
    "Hotel",
    "Flight",
    "Route",
    "AccommodationProvider",
    "FlightProvider",
    "RouteProvider",
    "AmadeusHotelProvider",
    "AmadeusFlightProvider",
    "GoogleRoutesProvider"
]

