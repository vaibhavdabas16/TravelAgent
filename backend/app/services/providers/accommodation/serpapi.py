"""SerpAPI Hotel Provider (Phase 2.3 - Week 5).

This module implements the AccommodationProvider interface using SerpAPI's
Google Hotels search functionality for price comparison and deal finding.

Key Features:
- Google Hotels scraping via SerpAPI
- Price comparison with Amadeus
- Additional hotel options not in Amadeus
- Review and rating aggregation
- Real-time pricing from Google
"""
import logging
from typing import List, Optional
from datetime import date

from serpapi import GoogleSearch

from app.config import settings
from app.services.providers.base import AccommodationProvider, Hotel

logger = logging.getLogger(__name__)


class SerpAPIHotelProvider(AccommodationProvider):
    """SerpAPI-based hotel provider for price intelligence.
    
    Uses SerpAPI to scrape Google Hotels for:
    - Price comparison
    - Additional hotel options
    - Reviews and ratings
    - Real-time availability
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the SerpAPI client.
        
        Args:
            api_key: SerpAPI API key (defaults to settings)
        """
        self.api_key = api_key or settings.serpapi_api_key
        self.provider_name = "serpapi"
        logger.info(f"SerpAPIHotelProvider initialized")
    
    async def search(
        self,
        destination: str,
        checkin_date: date,
        checkout_date: date,
        num_guests: int,
        filters: Optional[dict] = None
    ) -> List[Hotel]:
        """Search for hotels using SerpAPI Google Hotels.
        
        Args:
            destination: City name or location
            checkin_date: Check-in date
            checkout_date: Check-out date
            num_guests: Number of guests
            filters: Optional filters:
                - max_results: int (default 20)
                - currency: str (default "USD")
                - sort_by: str ("price", "rating", "reviews")
                - min_rating: float
        
        Returns:
            List of Hotel objects
        """
        filters = filters or {}
        max_results = filters.get('max_results', 20)
        currency = filters.get('currency', 'USD')
        sort_by = filters.get('sort_by', 8)  # 8 = lowest price
        
        logger.info(f"Searching Google Hotels for {destination}")
        
        try:
            # Build search parameters
            params = {
                "engine": "google_hotels",
                "q": destination,
                "check_in_date": checkin_date.strftime("%Y-%m-%d"),
                "check_out_date": checkout_date.strftime("%Y-%m-%d"),
                "adults": num_guests,
                "currency": currency,
                "gl": "us",  # Country
                "hl": "en",  # Language
                "sort_by": sort_by,
                "api_key": self.api_key
            }
            
            # Make API request
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Parse results
            hotels = []
            properties = results.get("properties", [])[:max_results]
            
            for prop in properties:
                hotel = self._parse_hotel_property(
                    prop,
                    checkin_date,
                    checkout_date,
                    currency
                )
                if hotel:
                    hotels.append(hotel)
            
            logger.info(f"Found {len(hotels)} hotels from SerpAPI")
            return hotels
            
        except Exception as e:
            logger.error(f"SerpAPI error: {e}")
            return []
    
    def _parse_hotel_property(
        self,
        prop: dict,
        checkin_date: date,
        checkout_date: date,
        currency: str
    ) -> Optional[Hotel]:
        """Parse SerpAPI hotel property into Hotel object.
        
        Args:
            prop: Property dict from SerpAPI
            checkin_date: Check-in date
            checkout_date: Check-out date
            currency: Currency code
        
        Returns:
            Hotel object or None
        """
        try:
            # Extract basic info
            name = prop.get("name", "Unknown Hotel")
            
            # Get coordinates
            gps_coordinates = prop.get("gps_coordinates", {})
            latitude = gps_coordinates.get("latitude")
            longitude = gps_coordinates.get("longitude")
            
            if not latitude or not longitude:
                logger.warning(f"Missing coordinates for {name}, skipping")
                return None
            
            # Get price info
            rate_per_night = prop.get("rate_per_night", {})
            if isinstance(rate_per_night, dict):
                price_str = rate_per_night.get("lowest", "0")
                # Remove currency symbols and commas
                price_str = price_str.replace("$", "").replace(",", "").replace("€", "").replace("£", "")
                try:
                    price_per_night = float(price_str)
                except:
                    price_per_night = 0.0
            else:
                price_per_night = 0.0
            
            # Calculate total price
            num_nights = (checkout_date - checkin_date).days
            total_price = price_per_night * num_nights
            
            # Get rating
            overall_rating = prop.get("overall_rating")
            if overall_rating:
                try:
                    rating = float(overall_rating)
                except:
                    rating = None
            else:
                rating = None
            
            # Get review count
            reviews = prop.get("reviews", 0)
            if isinstance(reviews, str):
                reviews = int(reviews.replace(",", "").replace("+", ""))
            
            # Get amenities
            amenities = prop.get("amenities", [])
            if isinstance(amenities, list):
                amenity_list = [a.get("name", a) if isinstance(a, dict) else str(a) for a in amenities[:10]]
            else:
                amenity_list = []
            
            # Get images
            images = prop.get("images", [])
            photo_url = images[0].get("thumbnail") if images else None
            
            # Get hotel class (stars)
            hotel_class = prop.get("hotel_class")
            
            # Link for booking
            link = prop.get("link")
            
            # Create standardized Hotel object - match the dataclass in base.py
            from app.services.providers.base import Hotel as HotelModel
            
            hotel = HotelModel(
                provider="serpapi",
                provider_id=prop.get("property_token", name.replace(" ", "_")),
                name=name,
                latitude=latitude,
                longitude=longitude,
                price_per_night=price_per_night,
                total_price=total_price,
                currency=currency,
                rating=rating,
                review_count=reviews,
                amenities=amenity_list,
                photo_url=photo_url,
                cancellation_policy=None,  # Not provided by SerpAPI
                offer_id=link,
                check_in=checkin_date.strftime("%Y-%m-%d"),
                check_out=checkout_date.strftime("%Y-%m-%d"),
                raw_data=prop
            )
            
            return hotel
            
        except Exception as e:
            logger.error(f"Error parsing hotel property: {e}")
            return None
    
    async def get_details(self, provider_id: str) -> Optional[Hotel]:
        """Get hotel details by ID.
        
        Note: SerpAPI doesn't have a direct details endpoint,
        so this returns None. Details are included in search results.
        
        Args:
            provider_id: Hotel provider ID
        
        Returns:
            None (not supported)
        """
        logger.warning("SerpAPI doesn't support get_details - use search instead")
        return None


# Singleton instance
_serpapi_hotel_provider: Optional[SerpAPIHotelProvider] = None


def get_serpapi_hotel_provider() -> SerpAPIHotelProvider:
    """Get or create the global SerpAPIHotelProvider instance."""
    global _serpapi_hotel_provider
    if _serpapi_hotel_provider is None:
        _serpapi_hotel_provider = SerpAPIHotelProvider()
    return _serpapi_hotel_provider

