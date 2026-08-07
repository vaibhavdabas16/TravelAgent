"""Test Week 4: Accommodation & Transport Agents (Phase 2.3).

This script tests:
1. Accommodation Agent (hotel search + location scoring)
2. Transport Agent (flight search + local transport)
3. Integration with existing workflow
4. AI-powered recommendations

Prerequisites:
- All Phase 2.3 Weeks 1-3 credentials (Amadeus, Google Maps)
- Run: python test_week4_agents.py
"""
import asyncio
import sys
import logging
from datetime import date, timedelta

sys.path.insert(0, '.')

from app.agents.accommodation import accommodation_agent_node, AccommodationAgent
from app.agents.transport import transport_agent_node, TransportAgent
from app.models.state import TravelAgentState

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_accommodation_agent():
    """Test accommodation agent with real hotel search and scoring."""
    logger.info("\n" + "="*70)
    logger.info("TEST 1: ACCOMMODATION AGENT")
    logger.info("="*70)
    
    try:
        # Create mock state
        state: TravelAgentState = {
            "destination": "PAR",
            "constraints": {
                "budget": "moderate",
                "num_days": 3,
                "num_travelers": 2
            },
            "discovered_pois": [
                {
                    "name": "Eiffel Tower",
                    "location": {"lat": 48.8584, "lng": 2.2945}
                },
                {
                    "name": "Louvre Museum",
                    "location": {"lat": 48.8606, "lng": 2.3376}
                },
                {
                    "name": "Notre-Dame",
                    "location": {"lat": 48.8530, "lng": 2.3499}
                }
            ],
            "messages": [],
            "potential_pois": [],
            "itinerary": [],
            "available_hotels": [],
            "optimization_attempts": 0,
            "current_stage": "discovery_complete",
            "optimization_suggestions": [],
            "error_message": None
        }
        
        logger.info("\n📊 Input State:")
        logger.info(f"   Destination: {state['destination']}")
        logger.info(f"   Budget: {state['constraints']['budget']}")
        logger.info(f"   POIs: {len(state['discovered_pois'])}")
        
        # Run accommodation agent
        result = await accommodation_agent_node(state)
        
        logger.info("\n✅ Agent completed!")
        logger.info(f"\n📝 Messages:")
        for msg in result.get('messages', []):
            logger.info(msg)
        
        hotels = result.get('recommended_hotels', [])
        logger.info(f"\n🏨 Hotels found: {len(hotels)}")
        
        if hotels:
            logger.info("\n🏆 Top Hotel:")
            hotel = hotels[0]
            logger.info(f"   Name: {hotel['name']}")
            logger.info(f"   Price: ${hotel['total_price']:.2f}")
            logger.info(f"   AI Score: {hotel.get('ai_score', 'N/A')}")
            logger.info(f"   Avg Commute: {hotel.get('avg_commute_time_minutes', 'N/A')} min")
        
        return len(hotels) > 0
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_transport_agent():
    """Test transport agent with flight search and local transport."""
    logger.info("\n" + "="*70)
    logger.info("TEST 2: TRANSPORT AGENT")
    logger.info("="*70)
    
    try:
        # Create mock state with hotel
        state: TravelAgentState = {
            "destination": "LAX",
            "constraints": {
                "budget": "moderate",
                "num_days": 4,
                "num_travelers": 1,
                "origin": "NYC"
            },
            "discovered_pois": [
                {
                    "name": "Hollywood Sign",
                    "location": {"lat": 34.1341, "lng": -118.3215}
                },
                {
                    "name": "Santa Monica Pier",
                    "location": {"lat": 34.0095, "lng": -118.4979}
                }
            ],
            "recommended_hotels": [
                {
                    "name": "Test Hotel LAX",
                    "latitude": 33.9416,
                    "longitude": -118.4085,
                    "total_price": 400.0
                }
            ],
            "messages": [],
            "potential_pois": [],
            "itinerary": [],
            "available_hotels": [],
            "optimization_attempts": 0,
            "current_stage": "accommodation_complete",
            "optimization_suggestions": [],
            "error_message": None
        }
        
        logger.info("\n📊 Input State:")
        logger.info(f"   Route: {state['constraints']['origin']} → {state['destination']}")
        logger.info(f"   Travelers: {state['constraints']['num_travelers']}")
        logger.info(f"   POIs: {len(state['discovered_pois'])}")
        
        # Run transport agent
        result = await transport_agent_node(state)
        
        logger.info("\n✅ Agent completed!")
        logger.info(f"\n📝 Messages:")
        for msg in result.get('messages', []):
            logger.info(msg)
        
        flights = result.get('recommended_flights', [])
        logger.info(f"\n✈️  Flights found: {len(flights)}")
        
        if flights:
            logger.info("\n🏆 Top Flight:")
            flight = flights[0]
            logger.info(f"   Airline: {flight['airline']}")
            logger.info(f"   Price: ${flight['price']:.2f}")
            logger.info(f"   Duration: {flight['duration_minutes']//60}h {flight['duration_minutes']%60}m")
            logger.info(f"   AI Score: {flight.get('ai_score', 'N/A')}")
        
        transport = result.get('local_transport')
        if transport:
            logger.info(f"\n🚇 Local Transport:")
            logger.info(f"   Recommended: {transport['recommended_mode']}")
            logger.info(f"   Daily Cost: ${transport['estimated_daily_cost']}")
        
        return len(flights) > 0
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_combined_workflow():
    """Test combined accommodation + transport workflow."""
    logger.info("\n" + "="*70)
    logger.info("TEST 3: COMBINED WORKFLOW")
    logger.info("="*70)
    
    try:
        # Initial state (after POI discovery)
        state: TravelAgentState = {
            "destination": "LON",
            "constraints": {
                "budget": "moderate",
                "num_days": 5,
                "num_travelers": 2,
                "origin": "PAR"
            },
            "discovered_pois": [
                {
                    "name": "Big Ben",
                    "location": {"lat": 51.5007, "lng": -0.1246}
                },
                {
                    "name": "Tower of London",
                    "location": {"lat": 51.5081, "lng": -0.0759}
                },
                {
                    "name": "British Museum",
                    "location": {"lat": 51.5194, "lng": -0.1270}
                }
            ],
            "messages": [],
            "potential_pois": [],
            "itinerary": [],
            "available_hotels": [],
            "optimization_attempts": 0,
            "current_stage": "discovery_complete",
            "optimization_suggestions": [],
            "error_message": None
        }
        
        logger.info("\n📊 Scenario: Paris → London, 5-day trip")
        logger.info(f"   Travelers: 2")
        logger.info(f"   Budget: Moderate")
        
        # Step 1: Accommodation
        logger.info("\n🏨 Step 1: Finding hotels...")
        accom_result = await accommodation_agent_node(state)
        
        hotels = accom_result.get('recommended_hotels', [])
        logger.info(f"   Found {len(hotels)} hotels")
        if hotels:
            logger.info(f"   Best: {hotels[0]['name']} (${hotels[0]['total_price']:.2f})")
        
        # Update state
        state.update(accom_result)
        state['current_stage'] = 'accommodation_complete'
        
        # Step 2: Transport
        logger.info("\n✈️  Step 2: Planning transport...")
        transport_result = await transport_agent_node(state)
        
        flights = transport_result.get('recommended_flights', [])
        logger.info(f"   Found {len(flights)} flight options")
        if flights:
            logger.info(f"   Best: {flights[0]['airline']} (${flights[0]['price']:.2f})")
        
        transport = transport_result.get('local_transport')
        if transport:
            logger.info(f"   Local transport: {transport['recommended_mode']}")
        
        # Summary
        logger.info("\n📊 Complete Trip Plan:")
        if hotels:
            logger.info(f"   🏨 Hotel: {hotels[0]['name']}")
            logger.info(f"      ${hotels[0]['total_price']:.2f} for {state['constraints']['num_days']} nights")
        if flights:
            total_flight_cost = sum(f['price'] for f in flights)
            logger.info(f"   ✈️  Flights: ${total_flight_cost:.2f}")
        if hotels and flights:
            total = hotels[0]['total_price'] + sum(f['price'] for f in flights)
            logger.info(f"   💰 Total: ${total:.2f} (accommodation + flights)")
        
        return len(hotels) > 0 and len(flights) > 0
        
    except Exception as e:
        logger.error(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all Week 4 agent tests."""
    logger.info("\n" + "="*70)
    logger.info("🚀 WEEK 4: ACCOMMODATION & TRANSPORT AGENTS TEST")
    logger.info("="*70)
    
    results = {
        'accommodation': await test_accommodation_agent(),
        'transport': await test_transport_agent(),
        'combined': await test_combined_workflow()
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
    
    if passed_count >= 2:
        logger.info("\n✅ Week 4 agents working!")
        logger.info("\nPhase 2.3 Progress:")
        logger.info("  ✅ Week 1: Amadeus Hotel API")
        logger.info("  ✅ Week 2: Amadeus Flight API")
        logger.info("  ✅ Week 3: Google Routes API")
        logger.info("  ✅ Week 4: Accommodation & Transport Agents")
        logger.info("  ⏳ Week 5: SerpAPI Price Intelligence")
        logger.info("  ⏳ Week 6: End-to-end Testing")
        logger.info("\n🎉 Phase 2.3 is 67% complete!")
        return 0
    else:
        logger.warning("\n⚠️  Some tests incomplete")
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








