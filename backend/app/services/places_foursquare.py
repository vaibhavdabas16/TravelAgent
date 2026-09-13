"""Foursquare Places + Geoapify backed replacement for GoogleMapsService.

Selected with MAPS_PROVIDER=foursquare. Neither provider needs a card on file:

- Foursquare Places  — POI search, details, photos, ratings, hours
- Geoapify           — geocoding and travel-time matrices

Every method returns the same dict shapes GoogleMapsService returns (place_id,
geometry.location, rating, user_ratings_total, types, price_level,
formatted_address, opening_hours, website, photos[].photo_reference), so the
discovery agent, scoring, optimizer and frontend are untouched. Differences
worth knowing:

- Foursquare rates places 0-10; we halve it so it reads as the 0-5 scale the
  rest of the code and the UI assume.
- Foursquare photos are plain URLs. We hand them out as "fsq:<base64url>"
  photo references so the existing /photos/{reference} proxy keeps working.
- Reviews are Foursquare "tips" (text only, no author rating).
"""
import asyncio
import base64
import logging
import re
from typing import Optional

import httpx

from app.config import settings
from app.services.cache import get_cache_service
from app.services.cost_tracker import get_cost_tracker

logger = logging.getLogger(__name__)

FSQ_NEW_BASE = "https://places-api.foursquare.com"
FSQ_V3_BASE = "https://api.foursquare.com/v3"
FSQ_API_VERSION = "2025-06-17"
GEOAPIFY_BASE = "https://api.geoapify.com/v1"

SEARCH_FIELDS = "categories,rating,stats,price,location,distance,website,tel,hours"
DETAIL_FIELDS = SEARCH_FIELDS + ",photos,tips,description"

# Foursquare category names -> the Google "types" the rest of the code keys on.
_CATEGORY_TYPES: list[tuple[str, str]] = [
    ("hotel", "lodging"), ("hostel", "lodging"), ("resort", "lodging"), ("bed & breakfast", "lodging"),
    ("inn", "lodging"), ("motel", "lodging"), ("guest house", "lodging"), ("ryokan", "lodging"),
    ("restaurant", "restaurant"), ("diner", "restaurant"), ("bistro", "restaurant"), ("steakhouse", "restaurant"),
    ("café", "cafe"), ("cafe", "cafe"), ("coffee", "cafe"), ("tea room", "cafe"), ("bakery", "bakery"),
    ("bar", "bar"), ("pub", "bar"), ("brewery", "bar"), ("lounge", "bar"), ("night club", "night_club"), ("nightclub", "night_club"),
    ("museum", "museum"), ("gallery", "art_gallery"), ("theater", "movie_theater"), ("theatre", "movie_theater"),
    ("park", "park"), ("garden", "park"), ("beach", "beach"), ("mountain", "natural_feature"),
    ("lake", "natural_feature"), ("river", "natural_feature"), ("waterfall", "natural_feature"), ("trail", "park"),
    ("temple", "place_of_worship"), ("shrine", "place_of_worship"), ("church", "church"), ("cathedral", "church"),
    ("mosque", "mosque"), ("monastery", "place_of_worship"), ("synagogue", "place_of_worship"),
    ("monument", "tourist_attraction"), ("landmark", "tourist_attraction"), ("historic", "tourist_attraction"),
    ("castle", "tourist_attraction"), ("palace", "tourist_attraction"), ("fort", "tourist_attraction"),
    ("scenic", "tourist_attraction"), ("lookout", "tourist_attraction"), ("tourist", "tourist_attraction"),
    ("plaza", "tourist_attraction"), ("bridge", "tourist_attraction"), ("tower", "tourist_attraction"),
    ("market", "market"), ("mall", "shopping_mall"), ("shopping", "shopping_mall"), ("store", "store"),
    ("shop", "store"), ("boutique", "clothing_store"),
    ("spa", "spa"), ("massage", "spa"), ("bath", "spa"), ("onsen", "spa"), ("gym", "gym"), ("yoga", "gym"),
    ("zoo", "zoo"), ("aquarium", "aquarium"), ("amusement", "amusement_park"), ("theme park", "amusement_park"),
    ("stadium", "stadium"), ("arena", "stadium"), ("library", "library"), ("cinema", "movie_theater"),
    ("music venue", "night_club"), ("concert", "night_club"), ("winery", "bar"), ("food", "food"),
]


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _types_from_categories(categories: list) -> list[str]:
    """Map Foursquare categories to Google-style type strings."""
    types: list[str] = []
    for cat in categories or []:
        name = (cat.get("name") or "").lower()
        if not name:
            continue
        for needle, gtype in _CATEGORY_TYPES:
            if needle in name and gtype not in types:
                types.append(gtype)
                break
        slug = _slug(name)
        if slug and slug not in types:
            types.append(slug)
    if not types:
        types.append("tourist_attraction")
    types.append("point_of_interest")
    return types


def encode_photo_reference(url: str) -> str:
    """Wrap a Foursquare photo URL so it survives as a path segment."""
    return "fsq:" + base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")


def decode_photo_reference(reference: str) -> Optional[str]:
    if not reference.startswith("fsq:"):
        return None
    token = reference[4:]
    token += "=" * (-len(token) % 4)
    try:
        return base64.urlsafe_b64decode(token.encode()).decode()
    except Exception:
        return None


_DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _opening_hours(hours: Optional[dict]) -> Optional[dict]:
    """Foursquare hours.regular -> Google opening_hours (periods + weekday_text)."""
    if not hours:
        return None
    regular = hours.get("regular") or []
    periods = []
    by_day: dict[int, list[str]] = {}
    for r in regular:
        day = r.get("day")  # 1 = Monday ... 7 = Sunday
        o, c = r.get("open"), r.get("close")
        if not isinstance(day, int) or not o or not c:
            continue
        gday = day % 7  # Google: 0 = Sunday
        periods.append({"open": {"day": gday, "time": o}, "close": {"day": gday, "time": c}})
        by_day.setdefault(day, []).append(f"{o[:2]}:{o[2:]} – {c[:2]}:{c[2:]}")
    weekday_text = [f"{_DAY_NAMES[d - 1]}: {', '.join(by_day[d])}" for d in sorted(by_day)] if by_day else None
    if hours.get("display") and not weekday_text:
        weekday_text = [hours["display"]]
    out: dict = {}
    if "open_now" in hours:
        out["open_now"] = hours["open_now"]
    if periods:
        out["periods"] = periods
    if weekday_text:
        out["weekday_text"] = weekday_text
    return out or None


class FoursquarePlacesService:
    """Drop-in for GoogleMapsService backed by Foursquare + Geoapify."""

    def __init__(self):
        if not settings.foursquare_api_key:
            raise RuntimeError("MAPS_PROVIDER=foursquare requires FOURSQUARE_API_KEY")
        if not settings.geoapify_api_key:
            raise RuntimeError("MAPS_PROVIDER=foursquare requires GEOAPIFY_API_KEY")

        key = settings.foursquare_api_key
        # Legacy v3 keys start with "fsq3"; service keys use the 2025 API.
        self._legacy = key.startswith("fsq3")
        self._base = FSQ_V3_BASE if self._legacy else FSQ_NEW_BASE
        headers = {"Accept": "application/json"}
        if self._legacy:
            headers["Authorization"] = key
        else:
            headers["Authorization"] = f"Bearer {key}"
            headers["X-Places-Api-Version"] = FSQ_API_VERSION

        self._fsq = httpx.Client(base_url=self._base, headers=headers, timeout=20.0)
        self._geo = httpx.Client(base_url=GEOAPIFY_BASE, timeout=20.0)
        self._geo_key = settings.geoapify_api_key
        self.cache = get_cache_service()
        self.cost_tracker = get_cost_tracker()
        logger.info("FoursquarePlacesService initialized (Foursquare %s API + Geoapify)", "v3" if self._legacy else "2025")

    # ------------------------------------------------------------------ geocode
    async def geocode(self, address: str, user_id: Optional[str] = None, trip_id: Optional[str] = None) -> Optional[dict]:
        cached = await self.cache.get_geocoding(address)
        if cached:
            return cached
        try:
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(None, lambda: self._geo.get(
                "/geocode/search", params={"text": address, "format": "json", "limit": 1, "apiKey": self._geo_key}
            ))
            resp.raise_for_status()
            results = resp.json().get("results") or []
            if not results:
                logger.warning(f"No geocoding results for: {address}")
                return None
            r = results[0]
            result = {"lat": r["lat"], "lng": r["lon"], "formatted_address": r.get("formatted") or address}
            await self.cache.set_geocoding(address, result)
            if user_id:
                await self.cost_tracker.track_call(trip_id, user_id, "geoapify", "geocoding")
            logger.info(f"Geocoded '{address}' to {result}")
            return result
        except Exception as e:
            logger.error(f"Geoapify geocoding error: {e}")
            return None

    # ------------------------------------------------------------------ places
    def _id_fields(self) -> str:
        return "fsq_id,name,geocodes," if self._legacy else "fsq_place_id,name,latitude,longitude,"

    def _search(self, params: dict) -> list:
        params = {**params, "fields": self._id_fields() + SEARCH_FIELDS}
        try:
            resp = self._fsq.get("/places/search", params=params)
            if resp.status_code != 200:
                logger.error(f"Foursquare search failed {resp.status_code}: {resp.text[:200]}")
                return []
            return [self._to_place(p) for p in resp.json().get("results", [])]
        except Exception as e:
            logger.error(f"Foursquare search error: {e}")
            return []

    def find_place(self, query: str, fields: Optional[list] = None) -> Optional[list]:
        results = self._search({"query": query, "limit": 5})
        return results or None

    def nearby_search(self, location: dict, radius: int, place_type: Optional[str] = None, keyword: Optional[str] = None) -> list:
        query = " ".join(x for x in [keyword, (place_type or "").replace("_", " ")] if x).strip()
        params = {"ll": f"{location['lat']},{location['lng']}", "radius": min(int(radius), 100000), "limit": 20}
        if query:
            params["query"] = query
        return self._search(params)

    def text_search(self, query: str, location: Optional[dict] = None, radius: Optional[int] = None) -> list:
        # Callers phrase queries like "top museums in Kyoto"; Foursquare wants
        # the thing and the place separately.
        q = query.strip()
        near = None
        m = re.match(r"^(?:top\s+|best\s+)?(.+?)\s+(?:in|near|around)\s+(.+)$", q, re.IGNORECASE)
        if m:
            q, near = m.group(1).strip(), m.group(2).strip()
        params: dict = {"query": q, "limit": 20}
        if location and radius:
            params["ll"] = f"{location['lat']},{location['lng']}"
            params["radius"] = min(int(radius), 100000)
        elif near:
            params["near"] = near
        results = self._search(params)
        logger.info(f"Foursquare found {len(results)} places for '{query}'")
        return results

    def place_details(self, place_id: str, fields: Optional[list] = None) -> Optional[dict]:
        try:
            resp = self._fsq.get(f"/places/{place_id}", params={"fields": self._id_fields() + DETAIL_FIELDS})
            if resp.status_code != 200:
                logger.warning(f"Foursquare details failed {resp.status_code} for {place_id}")
                return None
            data = resp.json()
            place = self._to_place(data)
            if not place.get("photos"):
                place["photos"] = self._photos(place_id)
            return place
        except Exception as e:
            logger.error(f"Foursquare details error: {e}")
            return None

    def _photos(self, place_id: str) -> list:
        try:
            resp = self._fsq.get(f"/places/{place_id}/photos", params={"limit": 1})
            if resp.status_code != 200:
                return []
            return [self._photo(p) for p in resp.json() if p.get("prefix") and p.get("suffix")]
        except Exception:
            return []

    @staticmethod
    def _photo(p: dict) -> dict:
        url = f"{p['prefix']}800x600{p['suffix']}"
        return {"photo_reference": encode_photo_reference(url), "width": p.get("width"), "height": p.get("height"), "url": url}

    def _to_place(self, p: dict) -> dict:
        """Foursquare place -> Google Places-shaped dict."""
        if self._legacy:
            pid = p.get("fsq_id")
            main = (p.get("geocodes") or {}).get("main") or {}
            lat, lng = main.get("latitude"), main.get("longitude")
        else:
            pid = p.get("fsq_place_id")
            lat, lng = p.get("latitude"), p.get("longitude")

        rating10 = p.get("rating")
        stats = p.get("stats") or {}
        loc = p.get("location") or {}
        photos = [self._photo(x) for x in (p.get("photos") or []) if x.get("prefix") and x.get("suffix")]
        tips = p.get("tips") or []

        out: dict = {
            "place_id": pid,
            "name": p.get("name"),
            "types": _types_from_categories(p.get("categories") or []),
            "geometry": {"location": {"lat": lat, "lng": lng}} if lat is not None and lng is not None else None,
            "formatted_address": loc.get("formatted_address") or ", ".join(
                x for x in [loc.get("address"), loc.get("locality"), loc.get("country")] if x
            ) or None,
            "vicinity": loc.get("address"),
            "rating": round(rating10 / 2, 1) if isinstance(rating10, (int, float)) else None,
            "user_ratings_total": stats.get("total_ratings") or stats.get("total_tips") or 0,
            "price_level": p.get("price"),
            "website": p.get("website"),
            "formatted_phone_number": p.get("tel"),
            "opening_hours": _opening_hours(p.get("hours")),
            "photos": photos,
            "reviews": [{"text": t.get("text"), "time": t.get("created_at")} for t in tips[:3] if t.get("text")],
            "business_status": "OPERATIONAL",
        }
        desc = p.get("description")
        if desc:
            out["editorial_summary"] = {"overview": desc}
        if p.get("distance") is not None:
            out["distance_meters"] = p["distance"]
        if photos:
            out["photo_url"] = photos[0]["url"]
        return out

    # ------------------------------------------------------------------ matrix
    @staticmethod
    def _mode(mode: str) -> str:
        return {"driving": "drive", "walking": "walk", "bicycling": "bicycle", "transit": "transit"}.get(mode, "drive")

    def get_distance_matrix(self, origins: list[dict], destinations: list[dict], mode: str = "driving") -> Optional[dict]:
        """Geoapify Route Matrix, reshaped to the Google Distance Matrix response."""
        try:
            body = {
                "mode": self._mode(mode),
                "sources": [{"location": [o["lng"], o["lat"]]} for o in origins],
                "targets": [{"location": [d["lng"], d["lat"]]} for d in destinations],
            }
            resp = self._geo.post("/routematrix", params={"apiKey": self._geo_key}, json=body)
            if resp.status_code != 200:
                logger.error(f"Geoapify routematrix failed {resp.status_code}: {resp.text[:200]}")
                return None
            data = resp.json()
            rows = []
            for row in data.get("sources_to_targets", []):
                elements = []
                for cell in row:
                    if cell.get("time") is None:
                        elements.append({"status": "ZERO_RESULTS"})
                    else:
                        t, d = int(cell["time"]), int(cell.get("distance") or 0)
                        elements.append({
                            "status": "OK",
                            "duration": {"value": t, "text": f"{max(1, round(t / 60))} mins"},
                            "distance": {"value": d, "text": f"{d / 1000:.1f} km"},
                        })
                rows.append({"elements": elements})
            return {"status": "OK", "rows": rows}
        except Exception as e:
            logger.error(f"Geoapify routematrix error: {e}")
            return None

    def calculate_travel_time_matrix(self, pois: list[dict], mode: str = "walking") -> Optional[list[list[int]]]:
        locations = [poi["location"] for poi in pois]
        result = self.get_distance_matrix(locations, locations, mode)
        if not result:
            return None
        n = len(pois)
        matrix = [[0] * n for _ in range(n)]
        for i, row in enumerate(result["rows"]):
            for j, el in enumerate(row["elements"]):
                matrix[i][j] = el["duration"]["value"] if el["status"] == "OK" else 3600
        return matrix
