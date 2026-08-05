import logging
import json
import math
from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.services.gemini import GeminiService
from app.services.search_api import SearchApiService
from app.models.state import TripConstraints

logger = logging.getLogger(__name__)

class ItineraryAgent:
    def __init__(self):
        self.llm = GeminiService()
        self.search_service = SearchApiService()

    async def generate_itinerary(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a detailed itinerary based on user selections.
        
        1. Clusters selections (POIs, Dining, Shopping) into days.
        2. Orders them logically (TSP-ish).
        3. Calculates transport between stops.
        4. Generates a narrative.
        """
        constraints = session_data.get("constraints", {})
        selections = session_data.get("selections", {})
        
        destination = constraints.get("destination")
        dates = constraints.get("dates") # e.g. "2025-06-01 to 2025-06-05"
        
        # 1. Gather all items with Category-based IDs
        items = []
        simple_id_map = {} # Map simple_id -> item
        
        # Comprehensive list of categories from frontend selections
        categories = ["pois", "dining", "shopping", "activities", "wellness", "entertainment", "nightlife", "accommodation"]
        
        for category in categories:
            category_items = selections.get(category, [])
            for i, item in enumerate(category_items):
                # Generate a category-based ID (e.g., poi_0, dining_1)
                # Use a short prefix for the category to keep it clean
                prefix_map = {
                    "pois": "poi",
                    "dining": "eat",
                    "shopping": "shop",
                    "activities": "act",
                    "wellness": "well",
                    "entertainment": "fun",
                    "nightlife": "night",
                    "accommodation": "stay"
                }
                prefix = prefix_map.get(category, category)
                simple_id = f"{prefix}_{i}"
                
                item["simple_id"] = simple_id
                item["type"] = category
                
                items.append(item)
                simple_id_map[simple_id] = item
                
        if not items:
            return {"error": "No items selected"}

        # 2. Cluster items into days (Using LLM for semantic clustering + location)
        day_plan = await self._cluster_and_order_items(items, constraints, simple_id_map)
        
        # 3. Enhance with Transport
        enhanced_plan = await self._add_transport_details(day_plan, destination)
        
        return {
            "trip_id": session_data.get("session_id"),
            "destination": destination,
            "dates": dates,
            "travelers": constraints.get("travelers", 2),
            "budget": constraints.get("budget", "moderate"),
            "tripStyle": constraints.get("tripStyle", "balanced"),
            "itinerary": enhanced_plan,
            "generated_at": datetime.utcnow().isoformat()
        }

    async def _cluster_and_order_items(self, items: List[Dict[str, Any]], constraints: Dict[str, Any], simple_id_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not items:
            return []

        # Create string representation using Simple IDs
        items_str = "\n".join([f"- ID: {item['simple_id']} | Name: {item.get('name')} ({item.get('type')}, {item.get('location', {}).get('formatted_address', 'Unknown')})" for item in items])
        
        prompt = f"""
        You are an expert travel planner. Organize the following selected items into a logical day-by-day itinerary for a trip to {constraints.get('destination')}.
        
        Trip Style: {constraints.get('tripStyle', 'balanced')}
        Dates: {constraints.get('dates', '3 days')}
        
        Selected Items:
        {items_str}
        
        Instructions:
        1. Group items by geographical proximity to minimize travel time.
        2. Create a balanced flow (e.g., Activity -> Lunch -> Shopping -> Dinner).
        3. Assign a theme to each day.
        4. Return a JSON object with a "days" key containing the array.
        
        JSON Format:
        {{
            "days": [
                {{
                    "day": 1,
                    "title": "Historical Exploration",
                    "stops": ["poi_0", "eat_1"]
                }}
            ]
        }}
        
        IMPORTANT: 
        1. Use the EXACT IDs (e.g., "poi_0", "eat_1") provided in the list.
        2. The "stops" array MUST be a list of these ID strings.
        3. Do not add generic items like "Lunch" or "Dinner" unless they are in the selected items list.
        """
        
        try:
            # DEBUG: Log the exact prompt being sent
            logger.info(f"Generated Itinerary Prompt:\n{prompt}")

            # Use generate_structured for reliable JSON
            day_plans_raw = self.llm.generate_structured(prompt)
            
            # DEBUG: Log the raw response from LLM
            logger.info(f"Raw LLM Response:\n{json.dumps(day_plans_raw, indent=2)}")
            
            # Extract days list
            if isinstance(day_plans_raw, dict):
                if "days" in day_plans_raw:
                    day_plans_raw = day_plans_raw["days"]
                elif "itinerary" in day_plans_raw:
                    day_plans_raw = day_plans_raw["itinerary"]
            
            if not isinstance(day_plans_raw, list):
                 # Fallback logic
                 if isinstance(day_plans_raw, dict):
                     for k, v in day_plans_raw.items():
                         if isinstance(v, list):
                             day_plans_raw = v
                             break
            
            if not isinstance(day_plans_raw, list):
                return [{"day": 1, "title": "My Trip", "stops": items}]
            
            final_plan = []
            for day in day_plans_raw:
                resolved_stops = []
                for stop_ref in day.get("stops", []):
                    # stop_ref should be the simple_id string "poi_0"
                    # But handle object case just in case LLM hallucinates structure
                    simple_id = None
                    if isinstance(stop_ref, str):
                        simple_id = stop_ref
                    elif isinstance(stop_ref, dict):
                        simple_id = stop_ref.get("id") or stop_ref.get("simple_id")
                    
                    if simple_id and simple_id in simple_id_map:
                        resolved_stops.append(simple_id_map[simple_id])
                    else:
                        logger.warning(f"Could not resolve stop reference: {stop_ref}")

                if resolved_stops:
                    final_plan.append({
                        "day": day.get("day"),
                        "title": day.get("title"),
                        "stops": resolved_stops
                    })
            
            return final_plan
            
        except Exception as e:
            logger.error(f"Error in itinerary clustering: {e}")
            # Fallback: Just put everything in Day 1
            return [{"day": 1, "title": "My Trip", "stops": items}]

    async def _add_transport_details(self, day_plan: List[Dict[str, Any]], destination: str) -> List[Dict[str, Any]]:
        # 1. Search for local transport providers once
        try:
            transport_search = await self.search_service.search(f"taxi services ride share apps public transport in {destination}")
            providers_summary = "Local options: "
            if "organic_results" in transport_search:
                providers = [r.get("title") for r in transport_search["organic_results"][:3]]
                providers_summary += ", ".join(providers)
        except Exception:
            providers_summary = "Local taxis and rideshares available."

        # 2. Calculate legs
        for day in day_plan:
            stops = day.get("stops", [])
            legs = []
            
            for i in range(len(stops) - 1):
                start = stops[i]
                end = stops[i+1]
                
                start_loc = start.get("location", {}) or start.get("geometry", {}).get("location", {})
                end_loc = end.get("location", {}) or end.get("geometry", {}).get("location", {})
                
                lat1, lng1 = start_loc.get("lat"), start_loc.get("lng")
                lat2, lng2 = end_loc.get("lat"), end_loc.get("lng")
                
                transport_info = {
                    "from": start.get("name"),
                    "to": end.get("name"),
                    "mode": "unknown",
                    "duration": "unknown",
                    "details": providers_summary,
                    "distance_km": None
                }
                
                if lat1 and lng1 and lat2 and lng2:
                    dist_km = self._haversine(lat1, lng1, lat2, lng2)
                    
                    if dist_km < 1.5:
                        transport_info["mode"] = "Walking"
                        transport_info["duration"] = f"{int(dist_km * 15)} mins" # Approx 4km/h
                        transport_info["details"] = "Scenic walk"
                    elif dist_km < 10.0:
                        transport_info["mode"] = "Taxi / Rideshare"
                        transport_info["duration"] = f"{int(dist_km * 3) + 5} mins driving" # Approx 20km/h + buffer
                        transport_info["details"] = providers_summary
                    else:
                        transport_info["mode"] = "Public Transit / Taxi"
                        transport_info["duration"] = f"{int(dist_km * 2) + 10} mins" # Approx 30km/h + buffer
                        transport_info["details"] = providers_summary
                        
                    transport_info["distance_km"] = round(dist_km, 1)
                
                legs.append(transport_info)
            
            day["transport_legs"] = legs
            
        return day_plan

    def _haversine(self, lat1, lon1, lat2, lon2):
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dlon / 2) * math.sin(dlon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
