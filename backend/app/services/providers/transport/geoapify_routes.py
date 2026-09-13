"""Geoapify routing provider — the no-card alternative to GoogleRoutesProvider.

Used when MAPS_PROVIDER=foursquare. Same RouteProvider contract:
get_route() for a single origin→destination, get_travel_time_matrix() for
the optimizer's N×M matrix. Geoapify's free tier (3,000 credits/day) covers
routing and the route matrix; no billing account is required.
"""
import asyncio
import logging
from typing import List, Optional

import httpx

from app.config import settings
from app.services.cache import get_cache_service
from app.services.cost_tracker import get_cost_tracker
from app.services.providers.base import Route, RouteProvider

logger = logging.getLogger(__name__)

GEOAPIFY_BASE = "https://api.geoapify.com/v1"

# Google-style mode names -> Geoapify modes.
_MODES = {"driving": "drive", "walking": "walk", "bicycling": "bicycle", "transit": "transit"}


class GeoapifyRoutesProvider(RouteProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.geoapify_api_key
        if not self.api_key:
            raise RuntimeError("GeoapifyRoutesProvider requires GEOAPIFY_API_KEY")
        self.client = httpx.Client(base_url=GEOAPIFY_BASE, timeout=25.0)
        self.cache = get_cache_service()
        self.cost_tracker = get_cost_tracker()
        logger.info("GeoapifyRoutesProvider initialized")

    async def get_route(
        self,
        origin: dict,
        destination: dict,
        mode: str = "transit",
        departure_time: Optional[str] = None,
        arrival_time: Optional[str] = None,
        options: Optional[dict] = None,
    ) -> Optional[Route]:
        o = f"{origin['lat']},{origin['lng']}"
        d = f"{destination['lat']},{destination['lng']}"
        cached = await self.cache.get_route(o, d, mode)
        if cached:
            try:
                return Route(**cached)
            except Exception:
                pass

        geo_mode = _MODES.get(mode, "drive")
        params = {"waypoints": f"{o}|{d}", "mode": geo_mode, "apiKey": self.api_key}
        try:
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: self.client.get("/routing", params=params))
            if resp.status_code != 200:
                logger.warning(f"Geoapify routing {geo_mode} failed {resp.status_code}: {resp.text[:160]}")
                return None
            features = resp.json().get("features") or []
            if not features:
                return None
            props = features[0].get("properties") or {}
            duration = int(props.get("time") or 0)
            distance = int(props.get("distance") or 0)
            if duration <= 0:
                return None

            steps = []
            for leg in props.get("legs") or []:
                for st in leg.get("steps") or []:
                    steps.append({
                        "travel_mode": geo_mode,
                        "duration": int(st.get("time") or 0),
                        "distance": int(st.get("distance") or 0),
                        "instructions": (st.get("instruction") or {}).get("text", ""),
                    })

            route = Route(
                provider="geoapify",
                origin=origin,
                destination=destination,
                mode=mode,
                duration_seconds=duration,
                distance_meters=distance,
                steps=steps,
            )
            await self.cache.set_route(o, d, mode, {
                "provider": route.provider, "origin": origin, "destination": destination, "mode": mode,
                "duration_seconds": duration, "distance_meters": distance, "steps": steps,
            })
            await self.cost_tracker.track_call(trip_id=None, user_id="system", service="geoapify", endpoint="routing")
            return route
        except Exception as e:
            logger.error(f"Geoapify routing error: {e}")
            return None

    async def get_travel_time_matrix(
        self, origins: List[dict], destinations: List[dict], mode: str = "transit"
    ) -> Optional[List[List[int]]]:
        body = {
            "mode": _MODES.get(mode, "drive"),
            "sources": [{"location": [o["lng"], o["lat"]]} for o in origins],
            "targets": [{"location": [d["lng"], d["lat"]]} for d in destinations],
        }
        try:
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None, lambda: self.client.post("/routematrix", params={"apiKey": self.api_key}, json=body)
            )
            if resp.status_code != 200:
                logger.error(f"Geoapify routematrix failed {resp.status_code}: {resp.text[:160]}")
                return None
            rows = resp.json().get("sources_to_targets") or []
            matrix = []
            for i, row in enumerate(rows):
                out = []
                for j, cell in enumerate(row):
                    t = cell.get("time")
                    if t is None:
                        logger.warning(f"No route from origin {i} to destination {j}")
                        out.append(3600)
                    else:
                        out.append(int(t))
                matrix.append(out)
            await self.cost_tracker.track_call(
                trip_id=None, user_id="system", service="geoapify", endpoint="routematrix",
                count=len(origins) * len(destinations),
            )
            return matrix
        except Exception as e:
            logger.error(f"Geoapify routematrix error: {e}")
            return None
