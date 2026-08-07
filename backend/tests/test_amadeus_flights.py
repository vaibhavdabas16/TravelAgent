"""Integration test for Amadeus Flight API (Phase 2.3 - Week 2).

This script tests the complete flight search workflow:
1. Initialize Amadeus flight provider
2. Search for one-way flights
3. Search for round-trip flights
4. Display results with pricing, stops, duration, CO2 emissions

Prerequisites:
- Set AMADEUS_API_KEY, AMADEUS_API_SECRET, AMADEUS_BASE_URL in .env
- Run: python test_amadeus_flights.py
"""
import asyncio
import sys
import logging
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, '.')

from app.services.providers.transport.amadeus_flights import get_amadeus_flight_provider

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def format_duration(minutes: int) -> str:
    """Format duration in minutes to human-readable string."""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def format_datetime(dt_str: str) -> str:
    """Format ISO datetime to readable string."""
    from datetime import datetime
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M')
    except:
        return dt_str


async def test_one_way_flights():
    """Test one-way flight search."""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: ONE-WAY FLIGHT SEARCH")
    logger.info("="*70)
    
    try:
        provider = get_amadeus_flight_provider()
        
        # Search: New York → Los Angeles
        origin = "NYC"
        destination = "LAX"
        departure = date.today() + timedelta(days=30)  # 30 days from now
        
        logger.info(f"\n✈️  Searching: {origin} → {destination}")
        logger.info(f"   Departure: {departure}")
        logger.info(f"   Passengers: 1")
        logger.info(f"   Cabin: Economy")
        
        flights = await provider.search(
            origin=origin,
            destination=destination,
            departure_date=departure,
            num_passengers=1,
            cabin_class="economy",
            filters={
                'max_results': 10,
                'currency': 'USD'
            }
        )
        
        logger.info(f"\n📊 Found {len(flights)} flight options")
        
        if flights:
            logger.info("\n🏆 Top 5 Flights (by price):")
            for i, flight in enumerate(flights[:5], 1):
                stops_text = "Direct" if flight.stops == 0 else f"{flight.stops} stop(s)"
                layover_text = ""
                if flight.layover_airports:
                    layover_text = f" via {', '.join(flight.layover_airports)}"
                
                logger.info(f"\n   {i}. {flight.airline} {flight.flight_number}")
                logger.info(f"      Route: {flight.origin} → {flight.destination}{layover_text}")
                logger.info(f"      Departure: {format_datetime(flight.departure_datetime)}")
                logger.info(f"      Arrival: {format_datetime(flight.arrival_datetime)}")
                logger.info(f"      Duration: {format_duration(flight.duration_minutes)}")
                logger.info(f"      Price: ${flight.price:.2f} {flight.currency}")
                logger.info(f"      Stops: {stops_text}")
                logger.info(f"      Cabin: {flight.cabin_class or 'N/A'}")
                logger.info(f"      Baggage: {flight.baggage_allowance or 'N/A'}")
                if flight.co2_emissions_kg:
                    logger.info(f"      CO2: {flight.co2_emissions_kg:.0f} kg")
        else:
            logger.warning("\n⚠️  No flights found. This could mean:")
            logger.warning("   - Using test environment with limited data")
            logger.warning("   - Route not available in test env")
            logger.warning("   - Try common routes like MAD-LON or PAR-NYC")
        
        return len(flights) > 0
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_round_trip_flights():
    """Test round-trip flight search."""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: ROUND-TRIP FLIGHT SEARCH")
    logger.info("="*70)
    
    try:
        provider = get_amadeus_flight_provider()
        
        # Search: Paris → New York (round-trip)
        origin = "PAR"
        destination = "NYC"
        departure = date.today() + timedelta(days=45)  # 45 days from now
        return_date = departure + timedelta(days=7)    # 7-day trip
        
        logger.info(f"\n✈️  Searching: {origin} ⇄ {destination}")
        logger.info(f"   Departure: {departure}")
        logger.info(f"   Return: {return_date}")
        logger.info(f"   Passengers: 2")
        logger.info(f"   Cabin: Economy")
        
        flights = await provider.search(
            origin=origin,
            destination=destination,
            departure_date=departure,
            return_date=return_date,
            num_passengers=2,
            cabin_class="economy",
            filters={
                'max_results': 10,
                'currency': 'USD'
            }
        )
        
        logger.info(f"\n📊 Found {len(flights)} flight segments")
        
        if flights:
            # Group by offer_id (outbound + return)
            offer_groups = {}
            for flight in flights:
                offer_id = flight.offer_id
                if offer_id not in offer_groups:
                    offer_groups[offer_id] = []
                offer_groups[offer_id].append(flight)
            
            logger.info(f"\n🏆 Top 3 Round-Trip Options:")
            for i, (offer_id, flight_pair) in enumerate(list(offer_groups.items())[:3], 1):
                total_price = sum(f.price for f in flight_pair)
                
                logger.info(f"\n   Option {i} - Total: ${total_price:.2f} USD")
                
                for idx, flight in enumerate(flight_pair, 1):
                    direction = "Outbound" if idx == 1 else "Return"
                    stops_text = "Direct" if flight.stops == 0 else f"{flight.stops} stop(s)"
                    
                    logger.info(f"\n      {direction}: {flight.airline} {flight.flight_number}")
                    logger.info(f"         {flight.origin} → {flight.destination}")
                    logger.info(f"         Depart: {format_datetime(flight.departure_datetime)}")
                    logger.info(f"         Arrive: {format_datetime(flight.arrival_datetime)}")
                    logger.info(f"         Duration: {format_duration(flight.duration_minutes)}")
                    logger.info(f"         Stops: {stops_text}")
                    logger.info(f"         Price: ${flight.price:.2f}")
        else:
            logger.warning("\n⚠️  No round-trip flights found")
            logger.warning("   - Try routes like MAD-LON, PAR-LON, or NYC-LAX")
        
        return len(flights) > 0
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_direct_flights_only():
    """Test direct flights filter."""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: DIRECT FLIGHTS ONLY")
    logger.info("="*70)
    
    try:
        provider = get_amadeus_flight_provider()
        
        # Search: Madrid → London (short route, likely direct)
        origin = "MAD"
        destination = "LON"
        departure = date.today() + timedelta(days=20)
        
        logger.info(f"\n✈️  Searching: {origin} → {destination} (Direct only)")
        logger.info(f"   Departure: {departure}")
        
        flights = await provider.search(
            origin=origin,
            destination=destination,
            departure_date=departure,
            num_passengers=1,
            cabin_class="economy",
            filters={
                'max_results': 5,
                'non_stop': True,  # Direct flights only
                'currency': 'EUR'
            }
        )
        
        logger.info(f"\n📊 Found {len(flights)} direct flights")
        
        if flights:
            # Verify all are direct
            all_direct = all(f.stops == 0 for f in flights)
            logger.info(f"\n✅ All flights are direct: {all_direct}")
            
            logger.info("\n🎯 Direct Flight Options:")
            for i, flight in enumerate(flights[:3], 1):
                logger.info(f"\n   {i}. {flight.airline} - €{flight.price:.2f}")
                logger.info(f"      Duration: {format_duration(flight.duration_minutes)}")
                logger.info(f"      {format_datetime(flight.departure_datetime)} → {format_datetime(flight.arrival_datetime)}")
        else:
            logger.warning("\n⚠️  No direct flights found for this route")
        
        return len(flights) > 0
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_business_class():
    """Test business class search."""
    logger.info("\n" + "="*70)
    logger.info("TEST 4: BUSINESS CLASS FLIGHTS")
    logger.info("="*70)
    
    try:
        provider = get_amadeus_flight_provider()
        
        origin = "NYC"
        destination = "LON"
        departure = date.today() + timedelta(days=60)
        
        logger.info(f"\n✈️  Searching: {origin} → {destination}")
        logger.info(f"   Cabin: Business Class")
        
        flights = await provider.search(
            origin=origin,
            destination=destination,
            departure_date=departure,
            num_passengers=1,
            cabin_class="business",
            filters={
                'max_results': 5,
                'currency': 'USD'
            }
        )
        
        logger.info(f"\n📊 Found {len(flights)} business class flights")
        
        if flights:
            logger.info("\n💼 Business Class Options:")
            for i, flight in enumerate(flights[:3], 1):
                logger.info(f"\n   {i}. {flight.airline}")
                logger.info(f"      Price: ${flight.price:.2f}")
                logger.info(f"      Cabin: {flight.cabin_class or 'N/A'}")
                logger.info(f"      Duration: {format_duration(flight.duration_minutes)}")
        
        return len(flights) > 0
        
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
    
    provider = get_amadeus_flight_provider()
    
    logger.info(f"\n✓ API Key: {provider.client_id[:10]}..." if provider.client_id else "❌ Missing")
    logger.info(f"✓ API Secret: {provider.client_secret[:10]}..." if provider.client_secret else "❌ Missing")
    logger.info(f"✓ Environment: {provider.client.hostname}")
    logger.info(f"✓ Cache: {'Connected' if provider.cache.connected else 'Not available'}")
    logger.info(f"✓ Cost Tracker: {'Initialized' if provider.cost_tracker else 'Not available'}")


async def main():
    """Run all flight tests."""
    logger.info("\n" + "="*70)
    logger.info("🚀 AMADEUS FLIGHT API INTEGRATION TESTS")
    logger.info("="*70)
    
    # Configuration check
    await test_provider_config()
    
    # Run tests
    results = {
        'one_way': await test_one_way_flights(),
        'round_trip': await test_round_trip_flights(),
        'direct_only': await test_direct_flights_only(),
        'business_class': await test_business_class()
    }
    
    # Summary
    logger.info("\n" + "="*70)
    logger.info("TEST SUMMARY")
    logger.info("="*70)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "⚠️  PARTIAL/FAIL"
        logger.info(f"{name.upper().replace('_', ' ')}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    logger.info("\n" + "="*70)
    logger.info(f"Results: {passed_count}/{total_count} tests passed")
    logger.info("="*70)
    
    if passed_count >= 2:  # At least 2 tests passing
        logger.info("\n✅ Flight API integration is working!")
        logger.info("\nNext steps:")
        logger.info("  1. Week 1 ✅: Amadeus Hotel API")
        logger.info("  2. Week 2 ✅: Amadeus Flight API")
        logger.info("  3. Week 3: Enhance Google Routes API provider")
        logger.info("  4. Week 4: Create Accommodation & Transport agents")
        return 0
    else:
        logger.warning("\n⚠️  Most tests failed")
        logger.info("\nTroubleshooting:")
        logger.info("  1. Verify Amadeus credentials in .env")
        logger.info("  2. Test environment has limited flight data")
        logger.info("  3. Try common routes: MAD-LON, PAR-NYC, NYC-LAX")
        logger.info("  4. Check date range (30-60 days in future)")
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








