"""
Simple automated test for Phase 2 - No user interaction required
"""

import sys
sys.path.insert(0, 'app')

from langchain_core.messages import HumanMessage
from app.agents.graph import get_travel_agent_graph


def test_tokyo_simple():
    """Test simple Tokyo trip."""
    print("\n" + "="*70)
    print("TEST: Simple Tokyo Trip")
    print("="*70)
    
    graph = get_travel_agent_graph()
    
    # Simple request with just 3 locations
    initial_state = {
        'messages': [
            HumanMessage(content="I want to visit Tokyo Tower and Senso-ji Temple in Tokyo today.")
        ],
        'optimization_params': {
            'day_start_hour': 9,
            'day_end_hour': 18,
            'travel_mode': 'walking',
            'strict_mode': False
        }
    }
    
    print("\n📨 Request: 'Visit Tokyo Tower and Senso-ji Temple in Tokyo'")
    print("🔄 Running workflow...\n")
    
    try:
        result = graph.invoke(initial_state)
        
        print("\n✅ Final Stage:", result.get('current_stage'))
        print("📊 POIs Found:", len(result.get('potential_pois', [])))
        print("📅 Itinerary Items:", len(result.get('itinerary', [])))
        
        if result.get('itinerary'):
            print("\n🎯 OPTIMIZED ITINERARY:")
            for i, item in enumerate(result['itinerary'], 1):
                print(f"  {i}. {item['place_name']}")
                print(f"     {item['start_time']} - {item['end_time']}")
            print("\n✅ SUCCESS: Itinerary created!")
            return True
        
        elif result.get('optimization_suggestions'):
            print(f"\n💡 Got {len(result['optimization_suggestions'])} suggestions")
            print("✅ SUCCESS: Adaptive handling working!")
            return True
        
        else:
            print("\n❌ FAILED: No itinerary or suggestions")
            if result.get('error_message'):
                print(f"   Error: {result['error_message']}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 PHASE 2 SIMPLE TEST\n")
    
    success = test_tokyo_simple()
    
    print("\n" + "="*70)
    if success:
        print("✅ TEST PASSED")
    else:
        print("❌ TEST FAILED")
    print("="*70 + "\n")

















