"""
Cost Tracking Service (Phase 2.4)

Tracks API call costs per trip and user.
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict

from app.services.cache import get_cache_service

logger = logging.getLogger(__name__)


@dataclass
class APICallCost:
    """Cost information for an API call."""
    service: str  # 'google_maps', 'gemini', 'places'
    endpoint: str  # 'geocoding', 'places_search', 'generate'
    count: int = 1
    estimated_cost: float = 0.0  # in USD


class CostTracker:
    """
    Tracks API costs per trip and user.
    
    Cost estimates based on Google Cloud pricing (as of 2025):
    - Geocoding: $5 per 1000 requests = $0.005 each
    - Places Search: $17 per 1000 requests = $0.017 each
    - Places Details: $17 per 1000 requests = $0.017 each
    - Distance Matrix: $5 per 1000 elements = $0.005 per element
    - Directions: $5 per 1000 requests = $0.005 each
    - Gemini Flash: $0.075 per 1M input tokens, $0.30 per 1M output tokens
    """
    
    # Cost per API call (USD)
    COSTS = {
        "google_maps": {
            "geocoding": 0.005,
            "places_search": 0.017,
            "places_details": 0.017,
            "distance_matrix_element": 0.005,
            "directions": 0.005,
        },
        "gemini": {
            "generate": 0.0001,  # Average per call (~1K tokens)
            "embedding": 0.00001,  # Much cheaper
        }
    }
    
    # Cost ceilings
    FREE_TIER_DAILY_LIMIT = 1.00  # $1 per day
    FREE_TIER_PER_TRIP_LIMIT = 0.10  # $0.10 per trip
    
    def __init__(self):
        """Initialize cost tracker."""
        self.cache = get_cache_service()
    
    async def track_call(
        self,
        trip_id: Optional[str],
        user_id: str,
        service: str,
        endpoint: str,
        count: int = 1
    ) -> float:
        """
        Track an API call and return estimated cost.
        
        Args:
            trip_id: Trip ID (optional)
            user_id: User ID
            service: Service name ('google_maps', 'gemini')
            endpoint: Endpoint name
            count: Number of calls (for bulk operations)
            
        Returns:
            float: Estimated cost in USD
        """
        cost = self.COSTS.get(service, {}).get(endpoint, 0.0) * count
        
        if not self.cache.connected:
            logger.debug(f"Cost tracking disabled: {service}.{endpoint} x{count} = ${cost:.4f}")
            return cost
        
        timestamp = datetime.utcnow().isoformat()
        
        try:
            # Track per trip
            if trip_id:
                trip_key = f"travel:cost:trip:{trip_id}"
                await self._increment_cost(trip_key, service, endpoint, count, cost)
            
            # Track per user (daily)
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
            user_key = f"travel:cost:user:{user_id}:{date_str}"
            await self._increment_cost(user_key, service, endpoint, count, cost)
            
            # Set expiry on user key (keep for 30 days)
            await self.cache.redis_client.expire(user_key, 2592000)
            
            logger.debug(f"Cost tracked: {service}.{endpoint} x{count} = ${cost:.4f}")
            return cost
            
        except Exception as e:
            logger.error(f"Cost tracking error: {e}")
            return cost
    
    async def _increment_cost(
        self,
        key: str,
        service: str,
        endpoint: str,
        count: int,
        cost: float
    ):
        """Increment cost counters in Redis hash."""
        await self.cache.redis_client.hincrby(key, f"{service}:{endpoint}:count", count)
        await self.cache.redis_client.hincrbyfloat(key, f"{service}:{endpoint}:cost", cost)
        await self.cache.redis_client.hincrbyfloat(key, "total_cost", cost)
    
    async def get_trip_cost(self, trip_id: str) -> Dict:
        """
        Get total cost for a trip.
        
        Args:
            trip_id: Trip ID
            
        Returns:
            Dict with cost breakdown
        """
        if not self.cache.connected:
            return {"connected": False}
        
        key = f"travel:cost:trip:{trip_id}"
        
        try:
            data = await self.cache.redis_client.hgetall(key)
            if not data:
                return {"trip_id": trip_id, "total_cost": 0.0, "calls": {}}
            
            # Parse the hash data
            total_cost = float(data.get("total_cost", 0.0))
            calls = {}
            
            for field, value in data.items():
                if field != "total_cost" and ":" in field:
                    service, endpoint, metric = field.rsplit(":", 2)
                    call_key = f"{service}:{endpoint}"
                    
                    if call_key not in calls:
                        calls[call_key] = {"count": 0, "cost": 0.0}
                    
                    if metric == "count":
                        calls[call_key]["count"] = int(value)
                    elif metric == "cost":
                        calls[call_key]["cost"] = float(value)
            
            return {
                "trip_id": trip_id,
                "total_cost": total_cost,
                "calls": calls,
                "within_limit": total_cost <= self.FREE_TIER_PER_TRIP_LIMIT
            }
            
        except Exception as e:
            logger.error(f"Get trip cost error: {e}")
            return {"error": str(e)}
    
    async def get_user_daily_cost(self, user_id: str, date: Optional[str] = None) -> Dict:
        """
        Get daily cost for a user.
        
        Args:
            user_id: User ID
            date: Date string (YYYY-MM-DD), defaults to today
            
        Returns:
            Dict with cost breakdown
        """
        if not self.cache.connected:
            return {"connected": False}
        
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        key = f"travel:cost:user:{user_id}:{date}"
        
        try:
            data = await self.cache.redis_client.hgetall(key)
            if not data:
                return {"user_id": user_id, "date": date, "total_cost": 0.0}
            
            total_cost = float(data.get("total_cost", 0.0))
            
            return {
                "user_id": user_id,
                "date": date,
                "total_cost": total_cost,
                "within_limit": total_cost <= self.FREE_TIER_DAILY_LIMIT
            }
            
        except Exception as e:
            logger.error(f"Get user daily cost error: {e}")
            return {"error": str(e)}
    
    async def check_cost_limit(
        self,
        user_id: str,
        trip_id: Optional[str] = None
    ) -> tuple[bool, float]:
        """
        Check if user/trip has exceeded cost limit.
        
        Args:
            user_id: User ID
            trip_id: Trip ID (optional)
            
        Returns:
            tuple: (within_limit, current_cost)
        """
        # Check daily user limit
        user_cost = await self.get_user_daily_cost(user_id)
        daily_total = user_cost.get("total_cost", 0.0)
        
        if daily_total >= self.FREE_TIER_DAILY_LIMIT:
            logger.warning(f"User {user_id} exceeded daily cost limit: ${daily_total:.2f}")
            return False, daily_total
        
        # Check trip limit if provided
        if trip_id:
            trip_cost = await self.get_trip_cost(trip_id)
            trip_total = trip_cost.get("total_cost", 0.0)
            
            if trip_total >= self.FREE_TIER_PER_TRIP_LIMIT:
                logger.warning(f"Trip {trip_id} exceeded cost limit: ${trip_total:.2f}")
                return False, trip_total
        
        return True, daily_total
    
    async def get_cost_stats(self) -> Dict:
        """Get overall cost statistics."""
        if not self.cache.connected:
            return {"connected": False}
        
        # This is a simple implementation
        # In production, you'd want a more sophisticated analytics system
        return {
            "connected": True,
            "message": "Cost tracking active",
            "daily_limit": self.FREE_TIER_DAILY_LIMIT,
            "per_trip_limit": self.FREE_TIER_PER_TRIP_LIMIT
        }


# Global instance
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """Get or create cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker








