"""Quick test with real Google Maps data - Tokyo itinerary"""
import sys
sys.path.insert(0, 'app')

from app.services.google_maps import GoogleMapsService
from app.services.optimizer import ItineraryOptimizer

print("\n🗾 TOKYO ITINERARY - Real Google Maps Data Test\n")

maps = GoogleMapsService()
opt = ItineraryOptimizer()

# Define POIs
poi_names = [
    "Shinjuku Station, Tokyo",
    "Tokyo Tower",
    "Senso-ji Temple, Tokyo",
    "Shibuya Crossing, Tokyo"
]

print("📍 Geocoding locations...")
pois = []
for i, name in enumerate(poi_names):
    coords = maps.geocode(name)
    if coords:
        print(f"   ✅ {name}: {coords['lat']:.6f}, {coords['lng']:.6f}")
        pois.append({
            'name': name.split(',')[0],
            'poi_id': f'poi_{i}',
            'location': {'lat': coords['lat'], 'lng': coords['lng']},
            'time_to_visit_minutes': 0 if i == 0 else 60
        })

print(f"\n🗺️  Calculating travel times (walking)...")
matrix = maps.calculate_travel_time_matrix(pois, 'walking')

if matrix:
    print("   Travel times:")
    for i in range(len(pois)):
        for j in range(len(pois)):
            if i != j:
                print(f"     {pois[i]['name']} → {pois[j]['name']}: {matrix[i][j]//60} min")

print(f"\n🔄 Optimizing itinerary...")
result = opt.optimize_day_itinerary(pois, matrix, 0, 9*3600, 22*3600)

if result and result.get('success'):
    print("\n✅ OPTIMIZED TOKYO ITINERARY:\n")
    for i, item in enumerate(result['schedule'], 1):
        print(f"{i}. {item['name']}")
        print(f"   {item['arrival_time']} - {item['departure_time']}")
        if 'travel_to_next_minutes' in item:
            print(f"   → {item['travel_to_next_minutes']} min to next\n")
    
    print(f"📊 Total travel: {result['total_travel_time_minutes']} min")
    print(f"   Total visit: {result['total_visit_time_minutes']} min")
    print(f"   Day ends: {result['day_end_time']}")
else:
    print("❌ No solution found")

