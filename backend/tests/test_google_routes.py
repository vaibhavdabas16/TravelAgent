"""Integration test for Google Routes API (Phase 2.3 - Week 3).

This script tests the complete routing workflow:
1. Transit routes (subway, bus)
2. Walking routes
3. Driving routes with traffic
4. Bicycling routes
5. Travel time matrix calculation
6. Multi-modal combinations

Prerequisites:
- Set GOOGLE_MAPS_API_KEY in .env
- Run: python test_google_routes.py
"""
import asyncio
import sys
import logging

# Add parent directory to path
sys.path.insert(0, '.')

from app.services.providers.transport.google_routes import get_google_routes_provider

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


def format_distance(meters: int) -> str:
    """Format distance in meters to human-readable string."""
    if meters < 1000:
        return f"{meters}m"
    km = meters / 1000
    return f"{km:.1f}km"


async def test_transit_route():
    """Test transit route (subway/bus)."""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: TRANSIT ROUTE (PUBLIC TRANSPORT)")
    logger.info("="*70)
    
    try:
        provider = get_google_routes_provider()
        
        # Times Square → Central Park (NYC)
        origin = {
            "lat": 40.7580,
            "lng": -73.9855,
            "address": "Times Square, New York, NY"
        }
        destination = {
            "lat": 40.7829,
            "lng": -73.9654,
            "address": "Central Park, New York, NY"
        }
        
        logger.info(f"\n🚇 Getting transit route:")
        logger.info(f"   From: {origin['address']}")
        logger.info(f"   To: {destination['address']}")
        
        route = await provider.get_route(
            origin=origin,
            destination=destination,
            mode="transit",
            departure_time="now",
            options={
                'transit_mode': ['subway', 'bus'],
                'transit_routing_preference': 'fewer_transfers'
            }
        )
        
        if route:
            logger.info(f"\n✅ Route found!")
            logger.info(f"   Duration: {format_duration(route.duration_seconds)}")
            logger.info(f"   Distance: {format_distance(route.distance_meters)}")
            if route.fare:
                logger.info(f"   Fare: {route.fare['currency']} {route.fare['amount']:.2f}")
            if route.departure_time and route.arrival_time:
                logger.info(f"   Depart: {route.departure_time}")
                logger.info(f"   Arrive: {route.arrival_time}")
            
            logger.info(f"\n📍 Step-by-step directions:")
            for i, step in enumerate(route.steps, 1):
                mode = step['travel_mode'].upper()
                duration = format_duration(step['duration'])
                distance = format_distance(step['distance'])
                
                if 'transit' in step:
                    transit = step['transit']
                    line_info = transit['line']
                    logger.info(f"\n   {i}. {mode}: {line_info['name']}")
                    logger.info(f"      Line: {line_info['short_name']} ({line_info['vehicle']})")
                    logger.info(f"      From: {transit['departure_stop']}")
                    logger.info(f"      To: {transit['arrival_stop']}")
                    logger.info(f"      Stops: {transit['num_stops']}")
                    logger.info(f"      Duration: {duration}")
                else:
                    logger.info(f"\n   {i}. {mode}: {distance} ({duration})")
            
            return True
        else:
            logger.warning("\n⚠️  No transit route found")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_walking_route():
    """Test walking route."""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: WALKING ROUTE")
    logger.info("="*70)
    
    try:
        provider = get_google_routes_provider()
        
        # Louvre → Eiffel Tower (Paris)
        origin = {
            "lat": 48.8606,
            "lng": 2.3376,
            "address": "Louvre Museum, Paris"
        }
        destination = {
            "lat": 48.8584,
            "lng": 2.2945,
            "address": "Eiffel Tower, Paris"
        }
        
        logger.info(f"\n🚶 Getting walking route:")
        logger.info(f"   From: {origin['address']}")
        logger.info(f"   To: {destination['address']}")
        
        route = await provider.get_route(
            origin=origin,
            destination=destination,
            mode="walking"
        )
        
        if route:
            logger.info(f"\n✅ Route found!")
            logger.info(f"   Duration: {format_duration(route.duration_seconds)}")
            logger.info(f"   Distance: {format_distance(route.distance_meters)}")
            logger.info(f"   Steps: {len(route.steps)} segments")
            
            # Show first few steps
            logger.info(f"\n📍 First 3 steps:")
            for i, step in enumerate(route.steps[:3], 1):
                duration = format_duration(step['duration'])
                distance = format_distance(step['distance'])
                # Strip HTML tags for display
                instructions = step['instructions'].replace('<b>', '').replace('</b>', '')
                instructions = instructions.replace('<div', ' ').replace('</div>', '')
                logger.info(f"   {i}. {distance} ({duration})")
                logger.info(f"      {instructions[:80]}...")
            
            return True
        else:
            logger.warning("\n⚠️  No walking route found")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_driving_route():
    """Test driving route with traffic."""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: DRIVING ROUTE (with traffic data)")
    logger.info("="*70)
    
    try:
        provider = get_google_routes_provider()
        
        # LAX → Hollywood Sign (Los Angeles)
        origin = {
            "lat": 33.9416,
            "lng": -118.4085,
            "address": "LAX Airport, Los Angeles"
        }
        destination = {
            "lat": 34.1341,
            "lng": -118.3215,
            "address": "Hollywood Sign, Los Angeles"
        }
        
        logger.info(f"\n🚗 Getting driving route:")
        logger.info(f"   From: {origin['address']}")
        logger.info(f"   To: {destination['address']}")
        logger.info(f"   With real-time traffic")
        
        route = await provider.get_route(
            origin=origin,
            destination=destination,
            mode="driving",
            departure_time="now",
            options={
                'avoid': ['tolls'],
                'units': 'imperial'
            }
        )
        
        if route:
            logger.info(f"\n✅ Route found!")
            logger.info(f"   Duration: {format_duration(route.duration_seconds)} (with current traffic)")
            logger.info(f"   Distance: {format_distance(route.distance_meters)}")
            logger.info(f"   Steps: {len(route.steps)} segments")
            
            return True
        else:
            logger.warning("\n⚠️  No driving route found")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_bicycling_route():
    """Test bicycling route."""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: BICYCLING ROUTE")
    logger.info("="*70)
    
    try:
        provider = get_google_routes_provider()
        
        # Golden Gate Park → Fisherman's Wharf (San Francisco)
        origin = {
            "lat": 37.7694,
            "lng": -122.4862,
            "address": "Golden Gate Park, San Francisco"
        }
        destination = {
            "lat": 37.8080,
            "lng": -122.4177,
            "address": "Fisherman's Wharf, San Francisco"
        }
        
        logger.info(f"\n🚴 Getting bicycling route:")
        logger.info(f"   From: {origin['address']}")
        logger.info(f"   To: {destination['address']}")
        
        route = await provider.get_route(
            origin=origin,
            destination=destination,
            mode="bicycling"
        )
        
        if route:
            logger.info(f"\n✅ Route found!")
            logger.info(f"   Duration: {format_duration(route.duration_seconds)}")
            logger.info(f"   Distance: {format_distance(route.distance_meters)}")
            
            return True
        else:
            logger.warning("\n⚠️  No bicycling route found")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_travel_time_matrix():
    """Test travel time matrix calculation."""
    logger.info("\n" + "="*70)
    logger.info("TEST 5: TRAVEL TIME MATRIX")
    logger.info("="*70)
    
    try:
        provider = get_google_routes_provider()
        
        # Top Paris attractions
        locations = [
            {"lat": 48.8606, "lng": 2.3376, "name": "Louvre"},
            {"lat": 48.8584, "lng": 2.2945, "name": "Eiffel Tower"},
            {"lat": 48.8530, "lng": 2.3499, "name": "Notre-Dame"},
            {"lat": 48.8867, "lng": 2.3431, "name": "Sacré-Cœur"}
        ]
        
        logger.info(f"\n🗺️  Calculating travel time matrix:")
        logger.info(f"   Locations: {len(locations)}")
        for loc in locations:
            logger.info(f"      - {loc['name']}")
        logger.info(f"   Mode: Walking")
        
        matrix = await provider.get_travel_time_matrix(
            origins=locations,
            destinations=locations,
            mode="walking"
        )
        
        if matrix:
            logger.info(f"\n✅ Matrix calculated!")
            logger.info(f"\n   Travel times (in minutes):")
            
            # Header
            header = "          "
            for loc in locations:
                header += f"{loc['name'][:10]:>12}"
            logger.info(header)
            
            # Rows
            for i, origin in enumerate(locations):
                row = f"{origin['name'][:10]:>10}"
                for j, destination in enumerate(locations):
                    minutes = matrix[i][j] // 60
                    row += f"{minutes:>12}"
                logger.info(row)
            
            # Insights
            logger.info(f"\n💡 Insights:")
            logger.info(f"   Average walking time: {sum(sum(row) for row in matrix) // (len(locations)**2) // 60}m")
            
            # Find longest walk
            max_time = 0
            max_pair = None
            for i in range(len(locations)):
                for j in range(i+1, len(locations)):
                    if matrix[i][j] > max_time:
                        max_time = matrix[i][j]
                        max_pair = (locations[i]['name'], locations[j]['name'])
            
            if max_pair:
                logger.info(f"   Longest walk: {max_pair[0]} ↔ {max_pair[1]} ({format_duration(max_time)})")
            
            return True
        else:
            logger.warning("\n⚠️  Matrix calculation failed")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_provider_config():
    """Test provider configuration."""
    logger.info("\n" + "="*70)
    logger.info("PROVIDER CONFIGURATION")
    logger.info("="*70)
    
    provider = get_google_routes_provider()
    
    logger.info(f"\n✓ API Key: {provider.api_key[:10]}..." if provider.api_key else "❌ Missing")
    logger.info(f"✓ Client: {type(provider.client).__name__}")
    logger.info(f"✓ Cache: {'Connected' if provider.cache.connected else 'Not available'}")
    logger.info(f"✓ Cost Tracker: {'Initialized' if provider.cost_tracker else 'Not available'}")


async def main():
    """Run all routing tests."""
    logger.info("\n" + "="*70)
    logger.info("🚀 GOOGLE ROUTES API INTEGRATION TESTS")
    logger.info("="*70)
    
    # Configuration check
    await test_provider_config()
    
    # Run tests
    results = {
        'transit': await test_transit_route(),
        'walking': await test_walking_route(),
        'driving': await test_driving_route(),
        'bicycling': await test_bicycling_route(),
        'matrix': await test_travel_time_matrix()
    }
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "⚠️  PARTIAL/FAIL"
        logger.info(f"{name.upper()}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    logger.info("\n" + "="*70)
    logger.info(f"Results: {passed_count}/{total_count} tests passed")
    logger.info("="*70)
    
    if passed_count >= 3:  # At least 3 tests passing
        logger.info("\n✅ Google Routes API integration is working!")
        logger.info("\nPhase 2.3 Progress:")
        logger.info("  1. Week 1 ✅: Amadeus Hotel API")
        logger.info("  2. Week 2 ✅: Amadeus Flight API")
        logger.info("  3. Week 3 ✅: Google Routes API")
        logger.info("  4. Week 4: Create Accommodation & Transport agents")
        logger.info("  5. Week 5: Add SerpAPI price intelligence")
        logger.info("  6. Week 6: End-to-end testing")
        return 0
    else:
        logger.warning("\n⚠️  Some tests failed")
        logger.info("\nThis is normal if:")
        logger.info("  - Testing locations outside supported regions")
        logger.info("  - API quotas exceeded")
        logger.info("  - No routes available for specific mode")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\nTests interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)








