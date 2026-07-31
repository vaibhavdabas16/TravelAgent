"""LangChain tools for itinerary optimization."""

import logging
from typing import List, Dict, Optional
from langchain_core.tools import tool

from app.services.optimizer import ItineraryOptimizer
from app.services.google_maps import get_google_maps_service

logger = logging.getLogger(__name__)


@tool
def optimize_itinerary(
    pois: List[Dict],
    start_location_name: str = "Hotel",
    travel_mode: str = "walking",
    day_start_hour: int = 9,
    day_end_hour: int = 22
) -> str:
    """
    Optimize a daily itinerary for visiting multiple POIs.
    
    This tool takes a list of points of interest (POIs) and generates an optimized
    visiting order that:
    - Minimizes travel time
    - Respects POI opening hours
    - Respects time needed at each location
    - Ensures the day fits within the specified time window
    
    Args:
        pois: List of POI dictionaries, each containing:
            - name: str (POI name)
            - poi_id: str (unique identifier)
            - location: dict with 'lat' and 'lng'
            - time_to_visit_minutes: int (optional, defaults to 60)
            - opening_time: str (optional, "HH:MM" format, defaults to day start)
            - closing_time: str (optional, "HH:MM" format, defaults to day end)
        start_location_name: Name of the starting location (e.g., "Hotel")
        travel_mode: Mode of travel ('walking', 'driving', 'bicycling', 'transit')
        day_start_hour: Hour to start the day (0-23)
        day_end_hour: Hour to end the day (0-23)
    
    Returns:
        A formatted string describing the optimized itinerary with times and travel info,
        or an error message if optimization fails.
    
    Example input:
        pois = [
            {
                "name": "Hotel",
                "poi_id": "hotel_1",
                "location": {"lat": 48.8566, "lng": 2.3522},
                "time_to_visit_minutes": 0
            },
            {
                "name": "Louvre Museum",
                "poi_id": "louvre_1",
                "location": {"lat": 48.8606, "lng": 2.3376},
                "time_to_visit_minutes": 180,
                "opening_time": "09:00",
                "closing_time": "18:00"
            }
        ]
    """
    try:
        if not pois or len(pois) < 2:
            return "Error: Need at least 2 locations to optimize an itinerary (starting point + at least 1 POI)."
        
        # Find the starting location index
        start_idx = 0
        for i, poi in enumerate(pois):
            if poi['name'].lower() == start_location_name.lower():
                start_idx = i
                break
        
        # Calculate travel time matrix using Google Maps
        maps_service = get_google_maps_service()
        travel_matrix = maps_service.calculate_travel_time_matrix(pois, mode=travel_mode)
        
        if travel_matrix is None:
            return "Error: Failed to calculate travel times between locations. Please check POI locations."
        
        # Convert time strings to seconds if present
        optimizer_service = ItineraryOptimizer()
        for poi in pois:
            if 'opening_time' in poi and isinstance(poi['opening_time'], str):
                poi['opening_time'] = optimizer_service.seconds_from_time_string(poi['opening_time'])
            if 'closing_time' in poi and isinstance(poi['closing_time'], str):
                poi['closing_time'] = optimizer_service.seconds_from_time_string(poi['closing_time'])
        
        # Run optimization
        result = optimizer_service.optimize_day_itinerary(
            pois=pois,
            travel_time_matrix=travel_matrix,
            start_location_idx=start_idx,
            day_start_time=day_start_hour * 3600,
            day_end_time=day_end_hour * 3600
        )
        
        if result is None or not result.get('success'):
            return "Error: Could not find a valid itinerary. Try reducing the number of locations or extending the day hours."
        
        # Format the result as a readable string
        output = f"✅ Optimized Itinerary for {len(pois)} locations:\n\n"
        
        for i, item in enumerate(result['schedule'], 1):
            output += f"{i}. {item['name']}\n"
            output += f"   📍 Arrive: {item['arrival_time']}\n"
            output += f"   🚪 Depart: {item['departure_time']}\n"
            output += f"   ⏱️  Duration: {item['visit_duration_minutes']} minutes\n"
            
            if 'travel_to_next_minutes' in item:
                output += f"   🚶 Travel to next: {item['travel_to_next_minutes']} minutes\n"
            output += "\n"
        
        output += f"📊 Summary:\n"
        output += f"   • Total travel time: {result['total_travel_time_minutes']} minutes\n"
        output += f"   • Total visit time: {result['total_visit_time_minutes']} minutes\n"
        output += f"   • Day ends at: {result['day_end_time']}\n"
        
        return output
        
    except Exception as e:
        logger.error(f"Error in optimize_itinerary tool: {e}", exc_info=True)
        return f"Error optimizing itinerary: {str(e)}"


@tool
def estimate_day_feasibility(
    num_pois: int,
    avg_visit_time_minutes: int = 60,
    avg_travel_time_minutes: int = 20,
    day_hours: int = 12
) -> str:
    """
    Estimate if a certain number of POIs can be visited in a day.
    
    This is a quick estimation tool to check feasibility before running
    the full optimization.
    
    Args:
        num_pois: Number of POIs to visit (excluding starting point)
        avg_visit_time_minutes: Average time to spend at each POI
        avg_travel_time_minutes: Average travel time between POIs
        day_hours: Number of hours available in the day
    
    Returns:
        A string indicating if the itinerary is feasible and recommendations.
    """
    total_visit_time = num_pois * avg_visit_time_minutes
    total_travel_time = (num_pois - 1) * avg_travel_time_minutes  # n-1 travels between n POIs
    total_time_needed = total_visit_time + total_travel_time
    day_minutes = day_hours * 60
    
    if total_time_needed <= day_minutes * 0.8:  # 80% to leave buffer
        return (f"✅ Feasible: {num_pois} POIs should fit comfortably in {day_hours} hours. "
                f"Estimated time: {total_time_needed // 60} hours {total_time_needed % 60} minutes.")
    elif total_time_needed <= day_minutes:
        return (f"⚠️ Tight: {num_pois} POIs might fit in {day_hours} hours, but it will be rushed. "
                f"Estimated time: {total_time_needed // 60} hours {total_time_needed % 60} minutes. "
                f"Consider reducing POIs or extending the day.")
    else:
        excess = total_time_needed - day_minutes
        suggested_pois = int(day_minutes * 0.8 / (avg_visit_time_minutes + avg_travel_time_minutes))
        return (f"❌ Not Feasible: {num_pois} POIs would require {total_time_needed // 60} hours "
                f"{total_time_needed % 60} minutes, but only {day_hours} hours available. "
                f"Excess: {excess // 60} hours {excess % 60} minutes. "
                f"Recommendation: Limit to {suggested_pois} POIs or extend day hours.")









