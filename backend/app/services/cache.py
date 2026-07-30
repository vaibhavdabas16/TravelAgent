"""
CacheService - Multi-layer caching with Redis (Phase 2.4)

Layer 1: API Response Cache (Places, Geocoding, Routes)
Layer 2: Session State Cache (Trip state)
Layer 3: LLM Response Cache (Deterministic prompts)
"""

import asyncio
import hashlib
import json
import logging
from datetime import timedelta
from typing import Any, Optional, Dict, Callable
from functools import wraps

import redis.asyncio as redis
from redis.asyncio import Redis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Centralized caching service with multiple layers and TTL strategies.
    
    Gracefully degrades if Redis is not available.
    """
    
    # TTL Constants (in seconds)
    TTL_PLACE_DETAILS = 86400  # 24 hours
    TTL_GEOCODING = 604800  # 7 days
    TTL_ROUTING = 300  # 5 minutes (traffic changes)
    TTL_LLM_RESPONSE = 2592000  # 30 days
    TTL_SESSION_STATE = None  # No expiry, deleted manually
    
    def __init__(self):
        """Initialize cache service."""
        self.redis_client: Optional[Redis] = None
        self.connected = False
        
    async def connect(self) -> bool:
        """
        Connect to Redis.
        
        Returns:
            bool: True if connected, False otherwise
        """
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            
            # Test connection
            await self.redis_client.ping()
            self.connected = True
            logger.info(f"✓ Redis connected: {settings.redis_host}:{settings.redis_port}")
            return True
            
        except Exception as e:
            logger.warning(f"Redis connection failed (graceful degradation): {e}")
            self.redis_client = None
            self.connected = False
            return False
    
    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
            logger.info("Redis connection closed")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from prefix and arguments.
        
        Args:
            prefix: Key prefix (e.g., 'place', 'geocode', 'route')
            *args: Positional arguments to hash
            **kwargs: Keyword arguments to hash
            
        Returns:
            str: Cache key
        """
        # Create a deterministic string from all arguments
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"travel:{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if not self.connected:
            return None
        
        try:
            value = await self.redis_client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.warning(f"Cache get error for {key}: {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (None = no expiry)
            
        Returns:
            bool: True if set successfully
        """
        if not self.connected:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            if ttl:
                await self.redis_client.setex(key, ttl, serialized)
            else:
                await self.redis_client.set(key, serialized)
            logger.debug(f"Cache SET: {key} (TTL: {ttl})")
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if deleted
        """
        if not self.connected:
            return False
        
        try:
            await self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for {key}: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.
        
        Args:
            pattern: Redis pattern (e.g., 'travel:trip:*')
            
        Returns:
            int: Number of keys deleted
        """
        if not self.connected:
            return 0
        
        try:
            keys = []
            async for key in self.redis_client.scan_iter(match=pattern):
                keys.append(key)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cache DELETE pattern {pattern}: {deleted} keys")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    # ==================== Layer 1: API Response Cache ====================
    
    async def get_place_details(self, place_id: str) -> Optional[Dict]:
        """Get cached place details."""
        key = self._generate_key("place", place_id)
        return await self.get(key)
    
    async def set_place_details(self, place_id: str, details: Dict) -> bool:
        """Cache place details for 24 hours."""
        key = self._generate_key("place", place_id)
        return await self.set(key, details, self.TTL_PLACE_DETAILS)
    
    async def get_geocoding(self, address: str) -> Optional[Dict]:
        """Get cached geocoding result."""
        key = self._generate_key("geocode", address.lower())
        return await self.get(key)
    
    async def set_geocoding(self, address: str, result: Dict) -> bool:
        """Cache geocoding result for 7 days."""
        key = self._generate_key("geocode", address.lower())
        return await self.set(key, result, self.TTL_GEOCODING)
    
    async def get_route(
        self,
        origin: tuple,
        destination: tuple,
        mode: str
    ) -> Optional[Dict]:
        """Get cached route calculation."""
        key = self._generate_key("route", origin, destination, mode)
        return await self.get(key)
    
    async def set_route(
        self,
        origin: tuple,
        destination: tuple,
        mode: str,
        result: Dict
    ) -> bool:
        """Cache route calculation for 5 minutes."""
        key = self._generate_key("route", origin, destination, mode)
        return await self.set(key, result, self.TTL_ROUTING)
    
    # ==================== Layer 2: Session State Cache ====================
    
    async def get_trip_state(self, trip_id: str) -> Optional[Dict]:
        """Get cached trip state."""
        key = f"travel:trip:{trip_id}:state"
        return await self.get(key)
    
    async def set_trip_state(self, trip_id: str, state: Dict) -> bool:
        """Cache trip state (no expiry)."""
        key = f"travel:trip:{trip_id}:state"
        return await self.set(key, state, self.TTL_SESSION_STATE)
    
    async def delete_trip_state(self, trip_id: str) -> bool:
        """Delete trip state from cache."""
        key = f"travel:trip:{trip_id}:state"
        return await self.delete(key)
    
    # ==================== Layer 3: LLM Response Cache ====================
    
    async def get_llm_response(
        self,
        prompt: str,
        model: str,
        **params
    ) -> Optional[str]:
        """Get cached LLM response."""
        key = self._generate_key("llm", prompt, model, **params)
        return await self.get(key)
    
    async def set_llm_response(
        self,
        prompt: str,
        model: str,
        response: str,
        **params
    ) -> bool:
        """Cache LLM response for 30 days."""
        key = self._generate_key("llm", prompt, model, **params)
        return await self.set(key, response, self.TTL_LLM_RESPONSE)
    
    # ==================== Cache Statistics ====================
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache info and stats
        """
        if not self.connected:
            return {
                "connected": False,
                "message": "Redis not available"
            }
        
        try:
            info = await self.redis_client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human"),
                "keys": await self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# ==================== Global Cache Instance ====================

_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


# ==================== Cache Decorator ====================

def cached(
    prefix: str,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds
        key_func: Optional function to generate cache key from args
        
    Example:
        @cached("my_func", ttl=300)
        async def my_function(arg1, arg2):
            return expensive_operation()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()
            
            if not cache.connected:
                return await func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator








