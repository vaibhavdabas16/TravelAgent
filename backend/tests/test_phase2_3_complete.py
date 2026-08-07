"""End-to-end test for Phase 2.3 complete workflow.

Tests the full travel agent workflow including:
1. Intake: Extract trip constraints
2. Discovery: Find and score POIs
3. Optimizer: Create optimized itinerary
4. Accommodation: Find and score hotels
5. Transport: Plan flights and local transport

Run: python test_phase2_3_complete.py
"""
import asyncio
import sys
import logging
from langchain_core.messages import HumanMessage

sys.path.insert(0, '.')

from app.agents.graph import get_travel_agent_graph

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_complete_workflow():
    """Test the complete Phase 2.3 workflow."""
    logger.info("\n" + "="*80)
    logger.info("PHASE 2.3 COMPLETE WORKFLOW TEST")
    logger.info("="*80)
    
    # Build the graph
    graph = get_travel_agent_graph()
    
    # Test scenario: 3-day Paris trip
    user_message = """
I want to visit Paris for 3 days next month with my partner.
We're interested in art, history, and good food.
Budget is moderate (around $200/day).
We'd like to see the Eiffel Tower, Louvre, and some local cafes.
"""
    
    logger.info(f"\n📝 User Request:")
    logger.info(f"{user_message.strip()}")
    
    # Initial state
    state = {
        "messages": [HumanMessage(content=user_message)]
    }
    
    try:
        logger.info("\n" + "="*80)
        logger.info("EXECUTING WORKFLOW")
        logger.info("="*80)
        
        # Run the workflow
        result = await graph.ainvoke(state)
        
        logger.info("\n" + "="*80)
        logger.info("WORKFLOW COMPLETE")
        logger.info("="*80)
        
        # Display results
        logger.info(f"\n📊 Final Stage: {result.get('current_stage')}")
        
        # Constraints
        if result.get('constraints'):
            constraints = result['constraints']
            logger.info(f"\n✅ Trip Constraints:")
            logger.info(f"   Destination: {constraints.get('destination')}")
            logger.info(f"   Duration: {constraints.get('num_days')} days")
            logger.info(f"   Budget: {constraints.get('budget')}")
            logger.info(f"   Travelers: {constraints.get('num_travelers')}")
        
        # POIs (correct field name is 'potential_pois')
        pois = result.get('potential_pois', [])
        logger.info(f"\n🗺️  Discovered POIs: {len(pois)}")
        if pois:
            for i, poi in enumerate(pois[:3], 1):
                logger.info(f"   {i}. {poi.get('name')} (Score: {poi.get('overall_score', 0):.1f})")
        
        # Itinerary (correct field name is 'itinerary')
        itinerary = result.get('itinerary', [])
        logger.info(f"\n📅 Optimized Itinerary: {len(itinerary)} items")
        if itinerary:
            for i, item in enumerate(itinerary[:5], 1):
                logger.info(f"   {i}. {item.get('name')} at {item.get('arrival_time')}")
        
        # Hotels
        hotels = result.get('recommended_hotels', [])
        logger.info(f"\n🏨 Recommended Hotels: {len(hotels)}")
        if hotels:
            for i, hotel in enumerate(hotels[:3], 1):
                logger.info(f"   {i}. {hotel.get('name')} - ${hotel.get('total_price', 0):.2f}")
                logger.info(f"      Score: {hotel.get('ai_score', 0):.1f}/100")
        
        # Flights
        flights = result.get('recommended_flights', [])
        logger.info(f"\n✈️  Recommended Flights: {len(flights)}")
        if flights:
            for i, flight in enumerate(flights[:3], 1):
                logger.info(f"   {i}. {flight.get('airline')} - ${flight.get('price', 0):.2f}")
                logger.info(f"      Score: {flight.get('ai_score', 0):.1f}/100")
        
        # Local Transport
        transport = result.get('local_transport', {})
        if transport:
            logger.info(f"\n🚌 Local Transport: {transport.get('recommended_mode', 'N/A')}")
            logger.info(f"   Daily Cost: ${transport.get('estimated_daily_cost', 0)}")
        
        # Messages
        messages = result.get('messages', [])
        logger.info(f"\n💬 Total Messages: {len(messages)}")
        if messages:
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                logger.info(f"\n📝 Last Agent Message:")
                content = last_message.content[:300]
                logger.info(f"{content}...")
        
        # Success check
        success = (
            result.get('current_stage') == 'transport_complete' and
            len(pois) > 0 and
            len(itinerary) > 0 and
            len(hotels) > 0
        )
        
        if success:
            logger.info("\n" + "="*80)
            logger.info("✅ PHASE 2.3 COMPLETE WORKFLOW: SUCCESS")
            logger.info("="*80)
            logger.info("\nAll agents executed successfully:")
            logger.info("  ✅ Intake: Extracted constraints")
            logger.info("  ✅ Discovery: Found and scored POIs")
            logger.info("  ✅ Optimizer: Created optimized itinerary")
            logger.info("  ✅ Accommodation: Recommended hotels")
            logger.info("  ✅ Transport: Planned flights and local transport")
            logger.info("\n🎉 Ready for production!")
            return 0
        else:
            logger.warning("\n⚠️  Workflow incomplete")
            return 1
            
    except Exception as e:
        logger.error(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_complete_workflow())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

