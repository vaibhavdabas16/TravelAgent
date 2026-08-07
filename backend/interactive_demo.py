"""
Interactive Demo for Itinerary Optimizer
Allows users to input their own locations and see real-time optimization
Uses real Google Maps API - no mocked data!
"""

import sys
sys.path.insert(0, 'app')

from app.services.google_maps import GoogleMapsService
from app.services.optimizer import ItineraryOptimizer
from datetime import datetime


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_step(number, text):
    """Print a step indicator."""
    print(f"\n{'='*70}")
    print(f"STEP {number}: {text}")
    print('='*70)


def get_location_from_user(prompt, default=None):
    """Get a location from user input."""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("  ⚠️  Please enter a valid location")


def get_time_from_user(prompt, default="09:00"):
    """Get time in HH:MM format."""
    user_input = input(f"{prompt} [{default}]: ").strip()
    time_str = user_input if user_input else default
    
    # Validate format
    try:
        parts = time_str.split(':')
        if len(parts) == 2:
            hour, minute = int(parts[0]), int(parts[1])
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
    except:
        pass
    
    print(f"  ⚠️  Invalid format, using default: {default}")
    return default


def get_number_from_user(prompt, default, min_val=None, max_val=None):
    """Get a number from user input."""
    user_input = input(f"{prompt} [{default}]: ").strip()
    
    try:
        value = int(user_input) if user_input else default
        if min_val is not None and value < min_val:
            value = min_val
        if max_val is not None and value > max_val:
            value = max_val
        return value
    except:
        print(f"  ⚠️  Invalid number, using default: {default}")
        return default


def interactive_demo():
    """Run interactive itinerary optimization demo."""
    print("\n" + "#"*70)
    print("  🗺️  INTERACTIVE ITINERARY OPTIMIZER DEMO")
    print("  Real Google Maps API Integration - No Mock Data!")
    print("#"*70)
    print(f"\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize services
    print("\n🔧 Initializing services...")
    try:
        maps_service = GoogleMapsService()
        optimizer_service = ItineraryOptimizer()
        print("✅ Google Maps service initialized")
        print("✅ OR-Tools optimizer initialized")
    except Exception as e:
        print(f"❌ Error initializing services: {e}")
        print("\n💡 Make sure GOOGLE_MAPS_API_KEY is set in .env file")
        return
    
    # Step 1: Get destination city
    print_step(1, "Choose Your Destination City")
    city = get_location_from_user("Enter city name", "Paris, France")
    
    # Step 2: Get starting location
    print_step(2, "Choose Your Starting Location (Hotel/Accommodation)")
    start_location = get_location_from_user(
        "Enter hotel name or address", 
        f"Hotel in {city.split(',')[0]}"
    )
    
    # Step 3: Get POIs
    print_step(3, "Add Points of Interest (POIs) to Visit")
    print("Enter POI names, addresses, or landmarks")
    print("(Press Enter on empty input when done)\n")
    
    poi_inputs = []
    poi_count = 1
    while True:
        poi_name = input(f"  POI #{poi_count} (or Enter to finish): ").strip()
        if not poi_name:
            if poi_count == 1:
                print("  ⚠️  You need at least one POI to optimize!")
                continue
            else:
                break
        
        # Get time to visit
        default_time = 60 if 'museum' in poi_name.lower() or 'tower' in poi_name.lower() else 45
        visit_time = get_number_from_user(
            f"    Time to spend at {poi_name} (minutes)",
            default_time, min_val=15, max_val=300
        )
        
        # Get opening/closing hours (optional)
        has_hours = input(f"    Does {poi_name} have specific opening hours? (y/N): ").strip().lower()
        opening_time = None
        closing_time = None
        
        if has_hours == 'y':
            opening_time = get_time_from_user("      Opening time", "09:00")
            closing_time = get_time_from_user("      Closing time", "18:00")
        
        poi_inputs.append({
            'name': poi_name,
            'visit_minutes': visit_time,
            'opening_time': opening_time,
            'closing_time': closing_time
        })
        poi_count += 1
    
    print(f"\n✅ Added {len(poi_inputs)} POIs")
    
    # Step 4: Set day parameters
    print_step(4, "Set Day Parameters")
    day_start_hour = get_number_from_user("Day start hour (0-23)", 9, 0, 23)
    day_end_hour = get_number_from_user("Day end hour (0-23)", 22, day_start_hour+1, 23)
    travel_mode = input("Travel mode (walking/driving/transit) [walking]: ").strip().lower()
    if travel_mode not in ['walking', 'driving', 'transit', 'bicycling']:
        travel_mode = 'walking'
    
    print(f"\n📋 Summary:")
    print(f"   • City: {city}")
    print(f"   • Starting point: {start_location}")
    print(f"   • POIs: {len(poi_inputs)}")
    print(f"   • Day: {day_start_hour:02d}:00 - {day_end_hour:02d}:00")
    print(f"   • Travel: {travel_mode}")
    
    input("\n Press Enter to start optimization...")
    
    # Step 5: Geocode all locations
    print_step(5, "Geocoding Locations")
    print("🔍 Getting coordinates from Google Maps...\n")
    
    all_pois = []
    
    # Geocode starting location
    print(f"📍 Geocoding: {start_location}")
    start_coords = maps_service.geocode(start_location)
    if not start_coords:
        print(f"❌ Could not find: {start_location}")
        return
    
    print(f"   ✅ {start_coords['formatted_address']}")
    print(f"   📍 {start_coords['lat']:.6f}, {start_coords['lng']:.6f}")
    
    all_pois.append({
        'name': start_location,
        'poi_id': 'start',
        'location': {'lat': start_coords['lat'], 'lng': start_coords['lng']},
        'time_to_visit_minutes': 0,
        'formatted_address': start_coords['formatted_address']
    })
    
    # Geocode POIs
    for i, poi_input in enumerate(poi_inputs, 1):
        print(f"\n📍 Geocoding: {poi_input['name']}")
        coords = maps_service.geocode(f"{poi_input['name']}, {city}")
        
        if not coords:
            print(f"   ⚠️  Not found, trying without city...")
            coords = maps_service.geocode(poi_input['name'])
        
        if not coords:
            print(f"   ❌ Could not find: {poi_input['name']}")
            print(f"   ⏭️  Skipping this location")
            continue
        
        print(f"   ✅ {coords['formatted_address']}")
        print(f"   📍 {coords['lat']:.6f}, {coords['lng']:.6f}")
        
        poi_data = {
            'name': poi_input['name'],
            'poi_id': f'poi_{i}',
            'location': {'lat': coords['lat'], 'lng': coords['lng']},
            'time_to_visit_minutes': poi_input['visit_minutes'],
            'formatted_address': coords['formatted_address']
        }
        
        if poi_input['opening_time']:
            poi_data['opening_time'] = poi_input['opening_time']
        if poi_input['closing_time']:
            poi_data['closing_time'] = poi_input['closing_time']
        
        all_pois.append(poi_data)
    
    if len(all_pois) < 2:
        print("\n❌ Need at least 2 locations (start + 1 POI) to optimize")
        return
    
    print(f"\n✅ Successfully geocoded {len(all_pois)} locations")
    
    # Step 6: Calculate travel times
    print_step(6, "Calculating Travel Times")
    print(f"🗺️  Getting real travel times via Google Maps ({travel_mode})...\n")
    
    travel_matrix = maps_service.calculate_travel_time_matrix(all_pois, mode=travel_mode)
    
    if not travel_matrix:
        print("❌ Failed to get travel times from Google Maps")
        return
    
    print("✅ Travel time matrix calculated\n")
    print("📊 Travel Times Between Locations:")
    print("-" * 70)
    
    for i, from_poi in enumerate(all_pois):
        for j, to_poi in enumerate(all_pois):
            if i != j:
                time_min = travel_matrix[i][j] // 60
                print(f"   {from_poi['name'][:30]:30} → {to_poi['name'][:30]:30} : {time_min:3d} min")
    
    # Step 7: Run optimization
    print_step(7, "Optimizing Itinerary")
    print("🔄 Running OR-Tools VRPTW solver...\n")
    
    # Convert time strings to seconds
    for poi in all_pois:
        if 'opening_time' in poi and isinstance(poi['opening_time'], str):
            poi['opening_time'] = optimizer_service.seconds_from_time_string(poi['opening_time'])
        if 'closing_time' in poi and isinstance(poi['closing_time'], str):
            poi['closing_time'] = optimizer_service.seconds_from_time_string(poi['closing_time'])
    
    result = optimizer_service.optimize_day_itinerary(
        pois=all_pois,
        travel_time_matrix=travel_matrix,
        start_location_idx=0,
        day_start_time=day_start_hour * 3600,
        day_end_time=day_end_hour * 3600
    )
    
    if not result or not result.get('success'):
        print("❌ Could not find a valid itinerary")
        print("💡 Try:")
        print("   • Reducing number of POIs")
        print("   • Extending day hours")
        print("   • Adjusting time constraints")
        return
    
    # Step 8: Display results
    print_step(8, "✅ OPTIMIZED ITINERARY")
    print()
    
    for i, item in enumerate(result['schedule'], 1):
        poi_data = all_pois[item['index']]
        
        print(f"{i}. {item['name']}")
        print(f"   📍 {poi_data.get('formatted_address', 'N/A')}")
        print(f"   🕐 Arrive: {item['arrival_time']}")
        print(f"   🚪 Depart: {item['departure_time']}")
        print(f"   ⏱️  Duration: {item['visit_duration_minutes']} minutes")
        
        if 'travel_to_next_minutes' in item:
            print(f"   🚶 {travel_mode.title()}: {item['travel_to_next_minutes']} min to next location")
        print()
    
    print("="*70)
    print("📊 SUMMARY")
    print("="*70)
    print(f"🚶 Total {travel_mode} time: {result['total_travel_time_minutes']} min ({result['total_travel_time_minutes']//60}h {result['total_travel_time_minutes']%60}m)")
    print(f"🎯 Total visit time: {result['total_visit_time_minutes']} min ({result['total_visit_time_minutes']//60}h {result['total_visit_time_minutes']%60}m)")
    print(f"⏰ Day ends at: {result['day_end_time']}")
    print(f"✅ All {len(all_pois)} locations visited!")
    
    print("\n" + "#"*70)
    print("  🎉 OPTIMIZATION COMPLETE!")
    print("#"*70)
    print("\n💡 This itinerary was created using:")
    print("   • Real coordinates from Google Maps Geocoding API")
    print(f"   • Real {travel_mode} times from Google Maps Distance Matrix API")
    print("   • OR-Tools VRPTW constraint solver")
    print("   • Opening hours and time window constraints")
    print("\n🚀 Ready for LangGraph agent integration!\n")


if __name__ == "__main__":
    try:
        interactive_demo()
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()









