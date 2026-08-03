"""Discovery Agent - Discovers and scores POIs based on trip constraints."""
import logging
from typing import Optional

from app.models.state import TripConstraints, POI
from app.tools.places import discover_places
from app.tools.scoring import score_poi

logger = logging.getLogger(__name__)


# Mapping from vibes to place types
VIBE_TO_PLACE_TYPES = {
    "cultural": ["museum", "art_gallery", "tourist_attraction", "historical_site"],
    "adventurous": ["park", "natural_feature", "tourist_attraction", "amusement_park"],
    "relaxed": ["spa", "park", "cafe", "beach"],
    "family": ["zoo", "aquarium", "amusement_park", "park"],
    "romantic": ["restaurant", "park", "tourist_attraction", "spa"],
    "party": ["night_club", "bar", "restaurant"],
    "foodie": ["restaurant", "cafe", "bakery", "food"],
    "shopping": ["shopping_mall", "store", "market"],
    "beach": ["beach", "water_park"],
    "nature": ["park", "natural_feature", "campground"],
    "urban": ["tourist_attraction", "museum", "restaurant", "shopping_mall"]
}


def get_place_types_for_vibe(vibe: Optional[str]) -> list[str]:
    """Determine which place types to search based on the trip vibe."""
    if not vibe:
        return ["tourist_attraction", "museum", "restaurant"]  # Default
    
    vibe_lower = vibe.lower()
    
    # Check for exact match
    if vibe_lower in VIBE_TO_PLACE_TYPES:
        return VIBE_TO_PLACE_TYPES[vibe_lower]
    
    # Check for partial matches
    for key, types in VIBE_TO_PLACE_TYPES.items():
        if key in vibe_lower or vibe_lower in key:
            return types
    
    # Default fallback
    return ["tourist_attraction", "museum", "restaurant"]


def sanitize_poi_name(name: str) -> str:
    """Sanitize POI name to handle comma-separated lists."""
    if not name:
        return name
    # If name contains ANY comma, it might be a list or a "Place, City" format.
    # However, for "Scotland", we are seeing lists like "A, B, C, D".
    # A safe heuristic: if it has > 2 commas, it's definitely a list.
    # If it has 1 comma, it might be "Place, City".
    # But the user reported "dalwhinnie, dalmore, oban, Talasker,Glen Livet" (4 commas).
    # My previous check was >= 2.
    # Let's try to be smarter: if the parts look like distinct names (e.g. capitalized), split.
    if ',' in name:
        parts = name.split(',')
        if len(parts) >= 2:
             # Just take the first one to be safe, as "Place, City" usually works with just "Place" too.
             return parts[0].strip()
    return name


async def discovery_agent(constraints: TripConstraints) -> dict:
    """
    Discovery Agent: Find and score POIs based on trip constraints.
    
    This agent:
    1. Determines what types of places to search for based on the vibe
    2. Discovers POIs using the Google Places API
    3. Scores each POI based on user constraints
    4. Returns the top-ranked POIs
    
    Args:
        constraints: Trip constraints from the Intake Agent
        
    Returns:
        Dictionary with:
        - potential_pois: List of scored POI dicts
        - discovery_summary: Summary string
        - error_message: Error message if something went wrong
    """
    try:
        destination = constraints.get('destination')
        if not destination:
            logger.warning("No destination provided to Discovery Agent")
            return {
                "potential_pois": [],
                "discovery_summary": "No destination specified",
                "error_message": "Please specify a destination"
            }
        
        vibe = constraints.get('vibe')
        budget = constraints.get('budget', 'moderate')
        must_see = constraints.get('must_see', [])
        
        logger.info(f"Starting discovery for {destination} with vibe: {vibe}")
        
        # Determine place types to search
        place_types = get_place_types_for_vibe(vibe)
        
        # Check if custom queries provided
        search_queries = constraints.get('search_queries')
        
        all_pois = []
        search_radius = 5000  # 5km radius
        
        if search_queries:
            # Use specific queries provided by QueryGenerator
            primary_query = search_queries.get('primary_query')
            fallback_query = search_queries.get('fallback_query')
            
            queries_to_try = [primary_query]
            if fallback_query and fallback_query != primary_query:
                queries_to_try.append(fallback_query)
                
            logger.info(f"Using custom queries: {queries_to_try}")
            
            for query in queries_to_try:
                try:
                    # Use text_search directly via places tool logic
                    # We need to access the service directly or update the tool to accept raw query
                    # For now, let's use the 'discover_places' tool but pass the query as 'place_type' 
                    # which we hacked in the previous step to do "top {place_type} in {location}"
                    # Wait, that hack forces "top ... in ...". 
                    # We should update the tool or use service directly.
                    # Let's use the service directly here for maximum control, or update the tool.
                    # Updating the tool is cleaner.
                    
                    # Actually, let's just use the tool's new text_search capability if we expose it.
                    # The tool currently takes 'place_type' and constructs "top {place_type} in {location}".
                    # If we pass the FULL query as 'place_type' and empty location, it might work if we adjust the tool.
                    # BUT, let's stick to the existing tool signature for now and just pass the query as place_type
                    # knowing that the tool will prepend "top " and append " in {location}".
                    # This is not ideal for "Romantic dinner...".
                    
                    # BETTER APPROACH: Use the service directly here since we are in the agent.
                    from app.services.google_maps import get_google_maps_service
                    service = get_google_maps_service()
                    
                    # Geocode first to get bias location
                    coords = await service.geocode(destination)
                    location_bias = {"lat": coords['lat'], "lng": coords['lng']} if coords else None
                    
                    pois = service.text_search(
                        query=query,
                        location=location_bias,
                        radius=search_radius
                    )
                    
                    if pois:
                        logger.info(f"Found {len(pois)} places with query '{query}'")
                        # Transform to expected format (enrichment needed?)
                        # The service returns raw places. We need to enrich them like the tool does.
                        # To save time/code, let's use the tool but we need to modify the tool to accept raw query.
                        pass 
                        
                        # Let's manually enrich top 10 to avoid blowing up context/quota
                        enriched_pois = []
                        for p in pois[:10]:
                            details = service.place_details(p['place_id'])
                            if details:
                                # CRITICAL: place_details might not return place_id if not requested in fields
                                # We must ensure it's present for deduplication downstream
                                details['place_id'] = p['place_id']
                                enriched_pois.append(details)
                        
                        all_pois.extend(enriched_pois)
                        
                        # If we found good results with primary, maybe we don't need fallback?
                        # Let's say if we got >= 5 results, we stop.
                        if len(all_pois) >= 5:
                            break
                            
                except Exception as e:
                    logger.error(f"Error searching with query '{query}': {e}")
                    continue
        else:
            # Default behavior: iterate over place types
            logger.info(f"Searching for place types: {place_types}")
            for place_type in place_types:
                try:
                    pois = await discover_places.ainvoke({
                        "location": destination,
                        "place_type": place_type,
                        "radius_meters": search_radius
                    })
                    if pois:
                        logger.info(f"Found {len(pois)} {place_type} places")
                        all_pois.extend(pois)
                except Exception as e:
                    logger.error(f"Error discovering {place_type} places: {e}")
                    continue
        
        if not all_pois:
            logger.warning(f"No POIs found for {destination}")
            return {
                "potential_pois": [],
                "discovery_summary": f"No places found in {destination}",
                "error_message": "Could not find any places matching your preferences"
            }
        
        # Remove duplicates by place_id and sanitize names
        unique_pois_dict = {}
        for poi in all_pois:
            place_id = poi.get('place_id')
            if place_id and place_id not in unique_pois_dict:
                # Sanitize name
                original_name = poi.get('name', '')
                logger.info(f"Processing POI: '{original_name}' (ID: {place_id})")
                
                sanitized = sanitize_poi_name(original_name)
                if original_name != sanitized:
                    logger.info(f"Sanitized POI name: '{original_name}' -> '{sanitized}'")
                poi['name'] = sanitized
                unique_pois_dict[place_id] = poi
                
        unique_pois = list(unique_pois_dict.values())
        logger.info(f"Found {len(unique_pois)} unique POIs after deduplication")
        
        # Filter irrelevant POIs using LLM
        filtered_pois = await filter_irrelevant_pois(unique_pois, destination)
        logger.info(f"Filtered {len(unique_pois) - len(filtered_pois)} irrelevant POIs")
        
        # Score each POI
        scored_pois = []
        for poi in filtered_pois:
            try:
                scored = await score_poi.ainvoke({
                    "poi": poi,
                    "user_constraints": {"budget": budget}
                })
                scored_pois.append(scored)
            except Exception as e:
                logger.error(f"Error scoring POI {poi.get('name')}: {e}")
                # Add with default score
                poi['ai_score'] = 50.0
                poi['score_breakdown'] = {}
                poi['recommendation_reason'] = "Good match for your trip."
                scored_pois.append(poi)
        
        # Sort by AI score (highest first)
        scored_pois.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
        
        # Return top 30 POIs
        top_pois = scored_pois[:30]
        
        # Create summary
        top_score = top_pois[0].get('ai_score', 0) if top_pois else 0
        summary = (
            f"Found {len(top_pois)} highly-rated places in {destination}. "
            f"Top recommendation: {top_pois[0].get('name')} (score: {top_score:.1f})"
        ) if top_pois else f"Found some places in {destination}"
        
        logger.info(f"Discovery complete: returning {len(top_pois)} POIs")
        
        return {
            "potential_pois": top_pois,
            "discovery_summary": summary,
            "error_message": None
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in Discovery Agent: {e}")
        return {
            "potential_pois": [],
            "discovery_summary": "An error occurred during discovery",
            "error_message": str(e)
        }


def filter_pois_by_must_see(pois: list[POI], must_see: list[str]) -> list[POI]:
    """
    Filter or boost POIs that match must-see requirements.
    
    Args:
        pois: List of POIs
        must_see: List of must-see items from user
        
    Returns:
        Filtered/boosted list of POIs
    """
    if not must_see:
        return pois
    
    # Create lowercase versions for matching
    must_see_lower = [item.lower() for item in must_see]
    
    boosted_pois = []
    for poi in pois:
        name = poi.get('name', '').lower()
        types = [t.lower() for t in poi.get('types', [])]
        
        # Check if POI matches any must-see item
        matches = False
        for must_see_item in must_see_lower:
            if must_see_item in name or any(must_see_item in t for t in types):
                matches = True
                # Boost the score
                current_score = poi.get('ai_score', 50)
                poi['ai_score'] = min(100, current_score + 15)  # Add 15 points, max 100
                logger.info(f"Boosted '{poi.get('name')}' for matching must-see: {must_see_item}")
                break
        
        boosted_pois.append(poi)
    
    # Re-sort after boosting
    boosted_pois.sort(key=lambda x: x.get('ai_score', 0), reverse=True)
    
    return boosted_pois


async def filter_irrelevant_pois(pois: list[dict], destination: str) -> list[dict]:
    """
    Filter out POIs that are not relevant to the destination using LLM.
    
    Args:
        pois: List of POI dicts
        destination: Target destination
        
    Returns:
        Filtered list of POIs
    """
    if not pois:
        return []
        
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import SystemMessage, HumanMessage
    from app.config import settings
    import json
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.gemini_api_key,
        temperature=0.0,
        response_mime_type="application/json"
    )
    
    # Prepare list for LLM
    poi_list = []
    for p in pois:
        poi_list.append({
            "id": p.get("place_id"),
            "name": p.get("name"),
            "address": p.get("formatted_address", "")
        })
    
    system_prompt = """You are a strict location validator. 
Your task is to filter a list of places and KEEP ONLY those that are actually located in or very near the target destination.

CRITICAL RULES:
1. Remove any places that are clearly in a different city or region (e.g., remove 'Taj Mahal' if destination is 'Manali').
2. Remove generic or low-quality results like 'Hotel X' if they are not relevant to a tourist visit, unless they are famous.
3. STRICTLY REMOVE NON-ATTRACTIONS:
   - Travel Agencies / Tour Operators (e.g., 'Global Trip Holidays', 'Manali Tour Package', 'Himachal Travels')
   - Taxi / Cab Services
   - Booking Offices / Ticket Counters
   - Mobile Shops / General Stores
   - ATMs / Banks
   - Government Offices (unless tourist spots)
4. Remove duplicate-sounding places if one looks like a spam listing.
5. For Indian locations, be extra vigilant about "Travels", "Holidays", "Adventures" (if it's an agency), and "Resort" (if it's just a hotel and not an attraction).

Return a JSON object with a 'valid_ids' list containing only the IDs of valid places."""

    user_prompt = f"""Target Destination: {destination}
    
Places to validate:
{json.dumps(poi_list, indent=2)}

Return JSON with 'valid_ids' list."""

    try:
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])
        
        result = json.loads(response.content)
        valid_ids = set(result.get("valid_ids", []))
        
        filtered = [p for p in pois if p.get("place_id") in valid_ids]
        return filtered
        
    except Exception as e:
        logger.error(f"Error filtering POIs with LLM: {e}")
        return pois  # Fallback to original list






