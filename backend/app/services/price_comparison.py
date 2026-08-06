"""Price Comparison Service (Phase 2.3 - Week 5).

This service aggregates hotel results from multiple providers (Amadeus, SerpAPI)
and identifies the best deals through intelligent price comparison.

Features:
- Multi-provider aggregation
- Duplicate detection (same hotel from different sources)
- Price comparison and best deal identification
- Savings calculation
- Provider diversity analysis
"""
import logging
from typing import List, Dict, Optional, Tuple
from datetime import date
from geopy.distance import geodesic

from app.services.providers.accommodation.amadeus import get_amadeus_hotel_provider
from app.services.providers.accommodation.serpapi import get_serpapi_hotel_provider
from app.services.providers.base import Hotel

logger = logging.getLogger(__name__)


class PriceComparisonService:
    """Service for comparing hotel prices across multiple providers."""
    
    def __init__(self):
        """Initialize the price comparison service."""
        self.amadeus_provider = get_amadeus_hotel_provider()
        self.serpapi_provider = get_serpapi_hotel_provider()
        logger.info("PriceComparisonService initialized")
    
    async def compare_hotels(
        self,
        destination: str,
        checkin_date: date,
        checkout_date: date,
        num_guests: int,
        filters: Optional[dict] = None
    ) -> Dict:
        """Compare hotel prices from multiple providers.
        
        Args:
            destination: Destination city/code
            checkin_date: Check-in date
            checkout_date: Check-out date
            num_guests: Number of guests
            filters: Optional filters
        
        Returns:
            Dict with:
                - all_hotels: Combined list of hotels
                - best_deals: Hotels with significant savings
                - price_comparison: Side-by-side comparisons
                - provider_stats: Statistics by provider
        """
        filters = filters or {}
        
        logger.info(f"Comparing prices for {destination}")
        
        # Search both providers in parallel
        import asyncio
        amadeus_hotels, serpapi_hotels = await asyncio.gather(
            self.amadeus_provider.search(
                destination=destination,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                num_guests=num_guests,
                filters=filters
            ),
            self.serpapi_provider.search(
                destination=destination,
                checkin_date=checkin_date,
                checkout_date=checkout_date,
                num_guests=num_guests,
                filters=filters
            ),
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(amadeus_hotels, Exception):
            logger.error(f"Amadeus search failed: {amadeus_hotels}")
            amadeus_hotels = []
        
        if isinstance(serpapi_hotels, Exception):
            logger.error(f"SerpAPI search failed: {serpapi_hotels}")
            serpapi_hotels = []
        
        logger.info(f"Found {len(amadeus_hotels)} from Amadeus, {len(serpapi_hotels)} from SerpAPI")
        
        # Find duplicates and compare prices
        matched_hotels, unmatched = self._match_hotels(amadeus_hotels, serpapi_hotels)
        
        # Identify best deals
        best_deals = self._identify_best_deals(matched_hotels, unmatched)
        
        # Generate statistics
        provider_stats = {
            "amadeus": {
                "total": len(amadeus_hotels),
                "avg_price": sum(h.total_price for h in amadeus_hotels) / len(amadeus_hotels) if amadeus_hotels else 0,
                "matched": len([m for m in matched_hotels if m['amadeus']])
            },
            "serpapi": {
                "total": len(serpapi_hotels),
                "avg_price": sum(h.total_price for h in serpapi_hotels) / len(serpapi_hotels) if serpapi_hotels else 0,
                "matched": len([m for m in matched_hotels if m['serpapi']])
            }
        }
        
        # Combine all unique hotels
        all_hotels = self._combine_hotels(amadeus_hotels, serpapi_hotels, matched_hotels)
        
        return {
            "all_hotels": all_hotels,
            "best_deals": best_deals,
            "matched_hotels": matched_hotels,
            "provider_stats": provider_stats
        }
    
    def _match_hotels(
        self,
        amadeus_hotels: List[Hotel],
        serpapi_hotels: List[Hotel]
    ) -> Tuple[List[Dict], List[Hotel]]:
        """Match hotels across providers using name and location.
        
        Args:
            amadeus_hotels: Hotels from Amadeus
            serpapi_hotels: Hotels from SerpAPI
        
        Returns:
            Tuple of (matched_hotels, unmatched_hotels)
        """
        matched = []
        unmatched = []
        used_serpapi_indices = set()
        
        for amadeus_hotel in amadeus_hotels:
            best_match = None
            best_match_idx = None
            best_similarity = 0
            
            for idx, serpapi_hotel in enumerate(serpapi_hotels):
                if idx in used_serpapi_indices:
                    continue
                
                # Calculate similarity
                similarity = self._calculate_similarity(amadeus_hotel, serpapi_hotel)
                
                if similarity > best_similarity and similarity > 0.7:  # 70% threshold
                    best_similarity = similarity
                    best_match = serpapi_hotel
                    best_match_idx = idx
            
            if best_match:
                # Found a match
                price_diff = amadeus_hotel.total_price - best_match.total_price
                savings_pct = (price_diff / amadeus_hotel.total_price * 100) if amadeus_hotel.total_price > 0 else 0
                
                matched.append({
                    "name": amadeus_hotel.name,
                    "amadeus": amadeus_hotel,
                    "serpapi": best_match,
                    "price_difference": price_diff,
                    "savings_percent": savings_pct,
                    "best_provider": "amadeus" if amadeus_hotel.total_price < best_match.total_price else "serpapi"
                })
                used_serpapi_indices.add(best_match_idx)
            else:
                # No match found, add to unmatched
                unmatched.append(amadeus_hotel)
        
        # Add unmatched SerpAPI hotels
        for idx, serpapi_hotel in enumerate(serpapi_hotels):
            if idx not in used_serpapi_indices:
                unmatched.append(serpapi_hotel)
        
        logger.info(f"Matched {len(matched)} hotels, {len(unmatched)} unique")
        return matched, unmatched
    
    def _calculate_similarity(self, hotel1: Hotel, hotel2: Hotel) -> float:
        """Calculate similarity score between two hotels (0-1).
        
        Args:
            hotel1: First hotel
            hotel2: Second hotel
        
        Returns:
            Similarity score from 0 to 1
        """
        # Name similarity (simple word overlap)
        name1_words = set(hotel1.name.lower().split())
        name2_words = set(hotel2.name.lower().split())
        
        if not name1_words or not name2_words:
            name_similarity = 0
        else:
            name_similarity = len(name1_words & name2_words) / len(name1_words | name2_words)
        
        # Location proximity (within 200m = same hotel)
        try:
            distance = geodesic(
                (hotel1.latitude, hotel1.longitude),
                (hotel2.latitude, hotel2.longitude)
            ).meters
            
            if distance < 50:
                location_similarity = 1.0
            elif distance < 200:
                location_similarity = 1.0 - (distance - 50) / 150
            else:
                location_similarity = 0.0
        except:
            location_similarity = 0.0
        
        # Weighted combination (name 60%, location 40%)
        similarity = name_similarity * 0.6 + location_similarity * 0.4
        
        return similarity
    
    def _identify_best_deals(
        self,
        matched_hotels: List[Dict],
        unmatched_hotels: List[Hotel]
    ) -> List[Dict]:
        """Identify best deals with significant savings.
        
        Args:
            matched_hotels: Hotels found in both providers
            unmatched_hotels: Hotels from single provider
        
        Returns:
            List of best deals sorted by savings
        """
        deals = []
        
        # Deals from matched hotels (price differences)
        for match in matched_hotels:
            if abs(match['savings_percent']) > 5:  # >5% difference
                deals.append({
                    "hotel": match[match['best_provider']],
                    "savings_amount": abs(match['price_difference']),
                    "savings_percent": abs(match['savings_percent']),
                    "cheaper_provider": match['best_provider'],
                    "comparison": {
                        "amadeus_price": match['amadeus'].total_price,
                        "serpapi_price": match['serpapi'].total_price
                    }
                })
        
        # Deals from unmatched (exclusive deals)
        # Find the top cheapest unmatched hotels
        unmatched_sorted = sorted(unmatched_hotels, key=lambda h: h.total_price)
        for hotel in unmatched_sorted[:5]:
            deals.append({
                "hotel": hotel,
                "savings_amount": 0,
                "savings_percent": 0,
                "cheaper_provider": hotel.provider,
                "exclusive": True,
                "comparison": None
            })
        
        # Sort by savings amount
        deals.sort(key=lambda d: d['savings_amount'], reverse=True)
        
        return deals[:10]  # Top 10 deals
    
    def _combine_hotels(
        self,
        amadeus_hotels: List[Hotel],
        serpapi_hotels: List[Hotel],
        matched_hotels: List[Dict]
    ) -> List[Hotel]:
        """Combine hotels from both providers, avoiding duplicates.
        
        For matched hotels, keep the cheaper option.
        
        Args:
            amadeus_hotels: Amadeus hotels
            serpapi_hotels: SerpAPI hotels
            matched_hotels: Matched hotel pairs
        
        Returns:
            Combined unique list of hotels
        """
        combined = []
        used_ids = set()
        
        # Add matched hotels (cheaper option)
        for match in matched_hotels:
            hotel = match[match['best_provider']]
            # Annotate with price comparison
            hotel.price_comparison = {
                "amadeus": match['amadeus'].total_price,
                "serpapi": match['serpapi'].total_price,
                "best": match['best_provider'],
                "savings": abs(match['price_difference'])
            }
            combined.append(hotel)
            used_ids.add(id(match['amadeus']))
            used_ids.add(id(match['serpapi']))
        
        # Add unmatched Amadeus hotels
        for hotel in amadeus_hotels:
            if id(hotel) not in used_ids:
                combined.append(hotel)
        
        # Add unmatched SerpAPI hotels
        for hotel in serpapi_hotels:
            if id(hotel) not in used_ids:
                combined.append(hotel)
        
        # Sort by price
        combined.sort(key=lambda h: h.total_price)
        
        logger.info(f"Combined {len(combined)} unique hotels")
        return combined


# Singleton instance
_price_comparison_service: Optional[PriceComparisonService] = None


def get_price_comparison_service() -> PriceComparisonService:
    """Get or create the global PriceComparisonService instance."""
    global _price_comparison_service
    if _price_comparison_service is None:
        _price_comparison_service = PriceComparisonService()
    return _price_comparison_service








