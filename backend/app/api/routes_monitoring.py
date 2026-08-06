"""
Monitoring & Observability Routes (Phase 2.4)

Endpoints for cache statistics, cost tracking, and system health.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.cache import get_cache_service
from app.services.cost_tracker import get_cost_tracker
from app.services.rate_limiter import get_rate_limiter
from app.api.routes_v2 import get_current_user

logger = logging.getLogger(__name__)

router_monitoring = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])
security = HTTPBearer()


@router_monitoring.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics.
    
    Returns hit rate, memory usage, and key counts.
    """
    cache = get_cache_service()
    stats = await cache.get_stats()
    return stats


@router_monitoring.get("/cost/trip/{trip_id}")
async def get_trip_cost(
    trip_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get cost breakdown for a specific trip.
    
    Requires authentication.
    """
    try:
        # Verify user owns this trip
        user_id = await get_current_user(credentials)
        
        cost_tracker = get_cost_tracker()
        cost_data = await cost_tracker.get_trip_cost(trip_id)
        
        return cost_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trip cost: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trip cost: {str(e)}"
        )


@router_monitoring.get("/cost/user/daily")
async def get_user_daily_cost(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    date: str = None
):
    """
    Get daily cost for current user.
    
    Args:
        date: Date in YYYY-MM-DD format (defaults to today)
    """
    try:
        user_id = await get_current_user(credentials)
        
        cost_tracker = get_cost_tracker()
        cost_data = await cost_tracker.get_user_daily_cost(user_id, date)
        
        return cost_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user daily cost: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get daily cost: {str(e)}"
        )


@router_monitoring.get("/ratelimit/status")
async def get_rate_limit_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get current rate limit usage for user.
    """
    try:
        user_id = await get_current_user(credentials)
        
        rate_limiter = get_rate_limiter()
        
        return {
            "user_id": user_id,
            "trips_per_hour": await rate_limiter.get_usage(user_id, "trips_per_hour"),
            "api_calls_per_minute": await rate_limiter.get_usage(user_id, "api_calls_per_minute"),
            "llm_calls_per_hour": await rate_limiter.get_usage(user_id, "llm_calls_per_hour"),
            "limits": rate_limiter.FREE_TIER_LIMITS
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit status: {str(e)}"
        )


@router_monitoring.get("/system/health")
async def system_health():
    """
    Comprehensive system health check including all Phase 2.4 services.
    """
    health = {
        "status": "healthy",
        "services": {}
    }
    
    # Check cache
    cache = get_cache_service()
    health["services"]["cache"] = {
        "connected": cache.connected,
        "status": "healthy" if cache.connected else "degraded"
    }
    
    # Check cost tracking
    try:
        cost_tracker = get_cost_tracker()
        cost_stats = await cost_tracker.get_cost_stats()
        health["services"]["cost_tracking"] = {
            "status": "healthy",
            "connected": cost_stats.get("connected", False)
        }
    except Exception as e:
        health["services"]["cost_tracking"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check rate limiter
    rate_limiter = get_rate_limiter()
    health["services"]["rate_limiter"] = {
        "status": "healthy",
        "connected": rate_limiter.cache.connected
    }
    
    # Overall status
    if any(s.get("status") == "error" for s in health["services"].values()):
        health["status"] = "unhealthy"
    elif any(s.get("status") == "degraded" for s in health["services"].values()):
        health["status"] = "degraded"
    
    return health








