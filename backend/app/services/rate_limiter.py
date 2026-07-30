"""
Rate Limiting Service (Phase 2.4)

Implements per-user and per-endpoint rate limiting using Redis.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.services.cache import get_cache_service

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using Redis for distributed rate limiting."""
    
    # Rate limits (requests per window)
    FREE_TIER_LIMITS = {
        "trips_per_hour": 10,
        "api_calls_per_minute": 60,
        "llm_calls_per_hour": 100
    }
    
    PREMIUM_TIER_LIMITS = {
        "trips_per_hour": 100,
        "api_calls_per_minute": 600,
        "llm_calls_per_hour": 1000
    }
    
    def __init__(self):
        """Initialize rate limiter."""
        self.cache = get_cache_service()
    
    async def check_rate_limit(
        self,
        user_id: str,
        action: str,
        tier: str = "free"
    ) -> tuple[bool, Optional[int]]:
        """
        Check if user has exceeded rate limit.
        
        Args:
            user_id: User ID
            action: Action type (e.g., 'trips_per_hour', 'api_calls_per_minute')
            tier: User tier ('free' or 'premium')
            
        Returns:
            tuple: (is_allowed, remaining_requests)
        """
        if not self.cache.connected:
            # If Redis is down, allow all requests
            logger.warning("Rate limiter disabled (Redis unavailable)")
            return True, None
        
        limits = self.FREE_TIER_LIMITS if tier == "free" else self.PREMIUM_TIER_LIMITS
        limit = limits.get(action, 1000)
        
        # Determine window duration
        if "per_minute" in action:
            window_seconds = 60
        elif "per_hour" in action:
            window_seconds = 3600
        elif "per_day" in action:
            window_seconds = 86400
        else:
            window_seconds = 3600  # default 1 hour
        
        # Redis key
        key = f"travel:ratelimit:{user_id}:{action}"
        
        try:
            # Get current count
            count = await self.cache.redis_client.get(key)
            current_count = int(count) if count else 0
            
            if current_count >= limit:
                logger.warning(f"Rate limit exceeded for user {user_id}: {action} ({current_count}/{limit})")
                return False, 0
            
            # Increment counter
            pipe = self.cache.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            await pipe.execute()
            
            remaining = limit - current_count - 1
            logger.debug(f"Rate limit OK for {user_id}: {action} ({current_count + 1}/{limit})")
            return True, remaining
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On error, allow request (fail open)
            return True, None
    
    async def get_usage(self, user_id: str, action: str) -> int:
        """
        Get current usage count for a user action.
        
        Args:
            user_id: User ID
            action: Action type
            
        Returns:
            int: Current count
        """
        if not self.cache.connected:
            return 0
        
        key = f"travel:ratelimit:{user_id}:{action}"
        
        try:
            count = await self.cache.redis_client.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Get usage error: {e}")
            return 0
    
    async def reset_user_limits(self, user_id: str):
        """Reset all rate limits for a user."""
        if not self.cache.connected:
            return
        
        pattern = f"travel:ratelimit:{user_id}:*"
        await self.cache.delete_pattern(pattern)
        logger.info(f"Reset rate limits for user {user_id}")


# Global instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter








