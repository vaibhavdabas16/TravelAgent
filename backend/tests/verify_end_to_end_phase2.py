import asyncio
import logging
from app.agents.graph import get_travel_agent_graph
from langchain_core.messages import HumanMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_end_to_end():
    print("=" * 50)
    print("VERIFYING END-TO-END FLOW (PHASE 2)")
    print("=" * 50)
    
    try:
        # Get the graph
        graph = get_travel_agent_graph()
        
        # Test input
        user_input = "Plan a 3-day trip to Paris for 2 people. We like art and good food. Budget is moderate."
        print(f"\n📝 User Input: {user_input}")
        
        # Initial state
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "current_stage": "start"
        }
        
        print("\n🚀 Starting Graph Execution...")
        
        # Run the graph
        final_state = await graph.ainvoke(initial_state)
        
        print("\n✅ Graph Execution Complete!")
        
        # Verify results
        print("\n🔍 Verifying Results:")
        
        # 1. Intake
        constraints = final_state.get('constraints')
        if constraints:
            print(f"   ✅ Intake: Extracted constraints for {constraints.get('destination')}")
        else:
            print("   ❌ Intake: Failed to extract constraints")
            
        # 2. Discovery
        pois = final_state.get('potential_pois')
        if pois:
            print(f"   ✅ Discovery: Found {len(pois)} POIs")
        else:
            print("   ❌ Discovery: No POIs found")
            
        # 3. Itinerary
        itinerary = final_state.get('itinerary')
        if itinerary:
            print(f"   ✅ Optimizer: Generated itinerary with {len(itinerary)} items")
        else:
            print("   ❌ Optimizer: No itinerary generated")
            
        # 4. Accommodation
        hotels = final_state.get('recommended_hotels')
        if hotels:
            print(f"   ✅ Accommodation: Found {len(hotels)} recommended hotels")
            print(f"      Top hotel: {hotels[0]['name']} (${hotels[0]['total_price']})")
        else:
            print("   ❌ Accommodation: No hotels found")
            
        # 5. Transport
        flights = final_state.get('recommended_flights')
        if flights:
            print(f"   ✅ Transport: Found {len(flights)} recommended flights")
            print(f"      Top flight: {flights[0]['airline']} (${flights[0]['price']})")
        else:
            print("   ⚠️ Transport: No flights found (might be expected if no origin provided)")
            
        local_transport = final_state.get('local_transport')
        if local_transport:
            print(f"   ✅ Transport: Local transport analysis available ({local_transport['recommended_mode']})")
        else:
            print("   ❌ Transport: No local transport analysis")
            print(f"      State keys: {list(final_state.keys())}")
            if final_state.get('error_message'):
                print(f"      Error Message: {final_state.get('error_message')}")
            if final_state.get('errors'):
                print(f"      Errors: {final_state.get('errors')}")
            
            # Check prerequisites
            print(f"      Prereq - POIs: {len(final_state.get('potential_pois', []))}")
            print(f"      Prereq - Hotels: {len(final_state.get('recommended_hotels', []))}")

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_end_to_end())
