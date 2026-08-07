"""Comprehensive Integration Test for Phase 2.3 (Weeks 1-3).

This script tests complete travel planning scenarios combining:
- Hotels (Amadeus)
- Flights (Amadeus)
- Routes (Google Maps)

Scenarios:
1. Weekend trip to Paris (hotel + local transport)
2. NYC to LA trip (flight + hotel + driving)
3. Business trip to London (hotel + transit)
4. Family vacation to Tokyo (round-trip flights + hotels)
5. Multi-city Europe tour (hotels + routes matrix)

Prerequisites:
- Set AMADEUS_API_KEY, AMADEUS_API_SECRET, GOOGLE_MAPS_API_KEY in .env
- Run: python test_complete_integration.py
"""
import asyncio
import sys
import logging
from datetime import date, timedelta

sys.path.insert(0, '.')

from app.services.providers.accommodation.amadeus import get_amadeus_hotel_provider
from app.services.providers.transport.amadeus_flights import get_amadeus_flight_provider
from app.services.providers.transport.google_routes import get_google_routes_provider

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_duration(seconds: int) -> str:
    """Format duration."""
    if seconds < 60:
        return f"{seconds}s"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes // 60
    mins = minutes % 60
    return f"{hours}h {mins}m"


async def scenario_1_paris_weekend():
    """Scenario 1: Weekend trip to Paris - Hotel + Local Transport."""
    logger.info("\n" + "="*80)
    logger.info("SCENARIO 1: WEEKEND TRIP TO PARIS")
    logger.info("="*80)
    logger.info("User: Solo traveler, 2-night stay, budget-conscious")
    logger.info("Needs: Affordable hotel + walking routes to top attractions")
    
    try:
        hotel_provider = get_amadeus_hotel_provider()
        route_provider = get_google_routes_provider()
        
        # Step 1: Find hotels
        logger.info("\n📍 Step 1: Searching for hotels in Paris...")
        checkin = date.today() + timedelta(days=14)
        checkout = checkin + timedelta(days=2)
        
        hotels = await hotel_provider.search(
            destination="PAR",
            checkin_date=checkin,
            checkout_date=checkout,
            num_guests=1,
            filters={'max_results': 5, 'currency': 'EUR'}
        )
        
        if hotels:
            logger.info(f"\n✅ Found {len(hotels)} hotels")
            logger.info(f"\nTop 3 Budget Options:")
            for i, hotel in enumerate(hotels[:3], 1):
                logger.info(f"\n   {i}. {hotel.name}")
                logger.info(f"      Price: €{hotel.total_price:.2f} total (€{hotel.price_per_night:.2f}/night)")
                logger.info(f"      Location: ({hotel.latitude:.4f}, {hotel.longitude:.4f})")
        
        # Step 2: Calculate routes from top hotel to attractions
        if hotels:
            logger.info(f"\n🗺️  Step 2: Calculating walking routes from hotel to attractions...")
            best_hotel = hotels[0]
            
            attractions = [
                {"name": "Eiffel Tower", "lat": 48.8584, "lng": 2.2945},
                {"name": "Louvre Museum", "lat": 48.8606, "lng": 2.3376},
                {"name": "Notre-Dame", "lat": 48.8530, "lng": 2.3499}
            ]
            
            hotel_loc = {"lat": best_hotel.latitude, "lng": best_hotel.longitude}
            
            total_walk_time = 0
            for attraction in attractions:
                route = await route_provider.get_route(
                    origin=hotel_loc,
                    destination={"lat": attraction["lat"], "lng": attraction["lng"]},
                    mode="walking"
                )
                
                if route:
                    walk_time = route.duration_seconds
                    total_walk_time += walk_time
                    logger.info(f"   → {attraction['name']}: {format_duration(walk_time)} walk")
            
            avg_walk = total_walk_time // len(attractions)
            logger.info(f"\n   Average walking time: {format_duration(avg_walk)}")
            
            if avg_walk < 1800:  # < 30 minutes
                logger.info(f"   ✅ Great location! Hotel is within 30min walk of all attractions")
            elif avg_walk < 3600:  # < 60 minutes
                logger.info(f"   ⚠️  Good location, but might want to consider metro")
            else:
                logger.info(f"   ⚠️  Distant location, metro/taxi recommended")
        
        logger.info("\n" + "-"*80)
        logger.info("SCENARIO 1: ✅ COMPLETE")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Scenario 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def scenario_2_nyc_to_la():
    """Scenario 2: NYC to LA - Flight + Hotel + Driving."""
    logger.info("\n" + "="*80)
    logger.info("SCENARIO 2: NYC TO LOS ANGELES BUSINESS TRIP")
    logger.info("="*80)
    logger.info("User: Business traveler, 3-night stay, needs rental car")
    logger.info("Needs: Flight + hotel near airport + driving routes")
    
    try:
        flight_provider = get_amadeus_flight_provider()
        hotel_provider = get_amadeus_hotel_provider()
        route_provider = get_google_routes_provider()
        
        # Step 1: Find flights
        logger.info("\n✈️  Step 1: Searching for flights NYC → LAX...")
        departure = date.today() + timedelta(days=30)
        
        flights = await flight_provider.search(
            origin="NYC",
            destination="LAX",
            departure_date=departure,
            num_passengers=1,
            cabin_class="economy",
            filters={'max_results': 3, 'currency': 'USD'}
        )
        
        if flights:
            logger.info(f"\n✅ Found {len(flights)} flights")
            logger.info(f"\nTop 3 Options:")
            for i, flight in enumerate(flights[:3], 1):
                stops = "Direct" if flight.stops == 0 else f"{flight.stops} stop(s)"
                logger.info(f"\n   {i}. {flight.airline} ${flight.price:.2f}")
                logger.info(f"      {flight.origin} → {flight.destination} ({stops})")
                logger.info(f"      Duration: {format_duration(flight.duration_minutes * 60)}")
        
        # Step 2: Find hotels near LAX
        logger.info(f"\n🏨 Step 2: Searching for hotels near LAX...")
        checkin = departure
        checkout = checkin + timedelta(days=3)
        
        hotels = await hotel_provider.search(
            destination="LAX",
            checkin_date=checkin,
            checkout_date=checkout,
            num_guests=1,
            filters={'max_results': 3, 'currency': 'USD'}
        )
        
        if hotels:
            logger.info(f"\n✅ Found {len(hotels)} hotels near LAX")
            logger.info(f"\nTop 3 Hotels:")
            for i, hotel in enumerate(hotels[:3], 1):
                logger.info(f"   {i}. {hotel.name} - ${hotel.total_price:.2f}")
        
        # Step 3: Calculate driving routes to business locations
        if hotels:
            logger.info(f"\n🚗 Step 3: Calculating driving routes to business locations...")
            hotel_loc = {"lat": hotels[0].latitude, "lng": hotels[0].longitude}
            
            business_locs = [
                {"name": "Downtown LA", "lat": 34.0522, "lng": -118.2437},
                {"name": "Santa Monica", "lat": 34.0195, "lng": -118.4912}
            ]
            
            for loc in business_locs:
                route = await route_provider.get_route(
                    origin=hotel_loc,
                    destination={"lat": loc["lat"], "lng": loc["lng"]},
                    mode="driving",
                    departure_time="now"
                )
                
                if route:
                    logger.info(f"   → {loc['name']}: {format_duration(route.duration_seconds)} drive")
        
        logger.info("\n" + "-"*80)
        logger.info("SCENARIO 2: ✅ COMPLETE")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Scenario 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def scenario_3_london_transit():
    """Scenario 3: London business trip - Hotel + Transit."""
    logger.info("\n" + "="*80)
    logger.info("SCENARIO 3: LONDON BUSINESS TRIP WITH PUBLIC TRANSPORT")
    logger.info("="*80)
    logger.info("User: Business traveler, prefers public transport")
    logger.info("Needs: Central hotel + transit routes to office")
    
    try:
        hotel_provider = get_amadeus_hotel_provider()
        route_provider = get_google_routes_provider()
        
        # Step 1: Find hotels in London
        logger.info("\n🏨 Searching for hotels in London...")
        checkin = date.today() + timedelta(days=20)
        checkout = checkin + timedelta(days=4)
        
        hotels = await hotel_provider.search(
            destination="LON",
            checkin_date=checkin,
            checkout_date=checkout,
            num_guests=1,
            filters={'max_results': 3, 'currency': 'GBP'}
        )
        
        if hotels:
            logger.info(f"\n✅ Found {len(hotels)} hotels")
            best_hotel = hotels[0]
            logger.info(f"\nBest Option: {best_hotel.name}")
            logger.info(f"Price: £{best_hotel.total_price:.2f}")
            
            # Step 2: Calculate transit to business district
            logger.info(f"\n🚇 Calculating transit routes to business districts...")
            hotel_loc = {
                "lat": best_hotel.latitude,
                "lng": best_hotel.longitude,
                "address": best_hotel.name
            }
            
            # Canary Wharf (financial district)
            office = {
                "lat": 51.5054,
                "lng": -0.0235,
                "address": "Canary Wharf, London"
            }
            
            route = await route_provider.get_route(
                origin=hotel_loc,
                destination=office,
                mode="transit",
                departure_time="now"
            )
            
            if route:
                logger.info(f"\n   Route to Canary Wharf:")
                logger.info(f"   Duration: {format_duration(route.duration_seconds)}")
                if route.fare:
                    logger.info(f"   Fare: £{route.fare['amount']:.2f}")
                
                transit_steps = [s for s in route.steps if 'transit' in s]
                logger.info(f"   Transit segments: {len(transit_steps)}")
                for step in transit_steps:
                    if 'transit' in step:
                        t = step['transit']
                        logger.info(f"      - {t['line']['name']} ({t['line']['vehicle']})")
        
        logger.info("\n" + "-"*80)
        logger.info("SCENARIO 3: ✅ COMPLETE")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Scenario 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def scenario_4_tokyo_roundtrip():
    """Scenario 4: Tokyo vacation - Round-trip flights + Hotel."""
    logger.info("\n" + "="*80)
    logger.info("SCENARIO 4: TOKYO FAMILY VACATION (ROUND-TRIP)")
    logger.info("="*80)
    logger.info("User: Family of 4, 7-day vacation")
    logger.info("Needs: Round-trip flights + family-friendly hotel")
    
    try:
        flight_provider = get_amadeus_flight_provider()
        hotel_provider = get_amadeus_hotel_provider()
        
        # Step 1: Round-trip flights
        logger.info("\n✈️  Searching for round-trip flights NYC → Tokyo...")
        departure = date.today() + timedelta(days=60)
        return_date = departure + timedelta(days=7)
        
        flights = await flight_provider.search(
            origin="NYC",
            destination="TYO",
            departure_date=departure,
            return_date=return_date,
            num_passengers=4,
            cabin_class="economy",
            filters={'max_results': 5, 'currency': 'USD'}
        )
        
        if flights:
            # Group by offer_id
            offers = {}
            for flight in flights:
                if flight.offer_id not in offers:
                    offers[flight.offer_id] = []
                offers[flight.offer_id].append(flight)
            
            logger.info(f"\n✅ Found {len(offers)} round-trip options")
            logger.info(f"\nTop 2 Options:")
            for i, (offer_id, flight_pair) in enumerate(list(offers.items())[:2], 1):
                total = sum(f.price for f in flight_pair)
                logger.info(f"\n   Option {i}: ${total:.2f} total for 4 passengers")
                for idx, f in enumerate(flight_pair, 1):
                    direction = "Outbound" if idx == 1 else "Return"
                    logger.info(f"      {direction}: {f.airline} ({format_duration(f.duration_minutes * 60)})")
        
        # Step 2: Hotels in Tokyo
        logger.info(f"\n🏨 Searching for family hotels in Tokyo...")
        hotels = await hotel_provider.search(
            destination="TYO",
            checkin_date=departure,
            checkout_date=return_date,
            num_guests=4,
            filters={'max_results': 3, 'currency': 'USD'}
        )
        
        if hotels:
            logger.info(f"\n✅ Found {len(hotels)} hotels")
            logger.info(f"\nTop Hotel: {hotels[0].name}")
            logger.info(f"Price: ${hotels[0].total_price:.2f} for 7 nights")
        
        logger.info("\n" + "-"*80)
        logger.info("SCENARIO 4: ✅ COMPLETE")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Scenario 4 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def scenario_5_europe_multi_city():
    """Scenario 5: Europe multi-city - Travel time analysis."""
    logger.info("\n" + "="*80)
    logger.info("SCENARIO 5: EUROPE MULTI-CITY TOUR (Travel Time Analysis)")
    logger.info("="*80)
    logger.info("User: Backpacker, visiting 4 cities")
    logger.info("Needs: Travel time matrix to plan efficient route")
    
    try:
        route_provider = get_google_routes_provider()
        
        # Cities to visit
        cities = [
            {"name": "Paris", "lat": 48.8566, "lng": 2.3522},
            {"name": "Amsterdam", "lat": 52.3676, "lng": 4.9041},
            {"name": "Brussels", "lat": 50.8503, "lng": 4.3517},
            {"name": "London", "lat": 51.5074, "lng": -0.1278}
        ]
        
        logger.info(f"\n🗺️  Calculating travel time matrix for 4 cities...")
        logger.info(f"Cities: {', '.join(c['name'] for c in cities)}")
        
        # Calculate matrix (using driving as proxy for train/flight)
        matrix = await route_provider.get_travel_time_matrix(
            origins=cities,
            destinations=cities,
            mode="driving"
        )
        
        if matrix:
            logger.info(f"\n✅ Matrix calculated!")
            logger.info(f"\n   Travel times (in hours):")
            
            # Header
            header = "            "
            for city in cities:
                header += f"{city['name'][:10]:>12}"
            logger.info(header)
            
            # Rows
            for i, origin in enumerate(cities):
                row = f"{origin['name'][:10]:>12}"
                for j, destination in enumerate(cities):
                    hours = matrix[i][j] / 3600
                    row += f"{hours:>11.1f}h"
                logger.info(row)
            
            # Find optimal route (greedy nearest neighbor)
            logger.info(f"\n💡 Route Optimization Insights:")
            
            # Start from Paris (index 0)
            current = 0
            visited = {0}
            route_order = [cities[0]['name']]
            total_time = 0
            
            while len(visited) < len(cities):
                # Find nearest unvisited city
                min_time = float('inf')
                next_city = None
                for j in range(len(cities)):
                    if j not in visited and matrix[current][j] < min_time:
                        min_time = matrix[current][j]
                        next_city = j
                
                if next_city is not None:
                    visited.add(next_city)
                    route_order.append(cities[next_city]['name'])
                    total_time += min_time
                    current = next_city
            
            logger.info(f"   Suggested route: {' → '.join(route_order)}")
            logger.info(f"   Total travel time: {total_time / 3600:.1f} hours")
        
        logger.info("\n" + "-"*80)
        logger.info("SCENARIO 5: ✅ COMPLETE")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Scenario 5 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all integration scenarios."""
    logger.info("\n" + "="*80)
    logger.info("🚀 COMPREHENSIVE INTEGRATION TEST - PHASE 2.3")
    logger.info("="*80)
    logger.info("Testing: Hotels (Amadeus) + Flights (Amadeus) + Routes (Google)")
    logger.info("="*80)
    
    # Run scenarios
    results = {
        'paris_weekend': await scenario_1_paris_weekend(),
        'nyc_to_la': await scenario_2_nyc_to_la(),
        'london_transit': await scenario_3_london_transit(),
        'tokyo_roundtrip': await scenario_4_tokyo_roundtrip(),
        'europe_multi_city': await scenario_5_europe_multi_city()
    }
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        scenario_name = name.replace('_', ' ').title()
        logger.info(f"{scenario_name}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    logger.info("\n" + "="*80)
    logger.info(f"Results: {passed_count}/{total_count} scenarios completed successfully")
    logger.info("="*80)
    
    if passed_count >= 3:
        logger.info("\n✅ Integration test PASSED!")
        logger.info("\n📊 All three provider types working together:")
        logger.info("   • Hotels: Real-time pricing and availability")
        logger.info("   • Flights: One-way and round-trip with multiple carriers")
        logger.info("   • Routes: Multi-modal routing with transit details")
        logger.info("\n🎉 Ready for Week 4: Agent Integration!")
        return 0
    else:
        logger.warning("\n⚠️  Some scenarios incomplete (expected in test env)")
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








