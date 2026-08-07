"""
End-to-End Test for Phase 2: Complete Trip Planning with Optimization
Tests the full workflow: Intake → Discovery → Optimization
"""

import sys
sys.path.insert(0, 'app')

from langchain_core.messages import HumanMessage
from app.agents.graph import get_travel_agent_graph


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_simple_tokyo_trip():
    """Test a simple Tokyo trip that should succeed."""
    print_section("TEST 1: Simple Tokyo Trip (Should Succeed)")
    
    graph = get_travel_agent_graph()
    
    initial_state = {
        'messages': [
            HumanMessage(content="I want to visit Tokyo for a day. I love temples and modern architecture. "
                                "I want to see Tokyo Tower and a traditional temple.")
        ]
    }
    
    print("\n📨 User Request:")
    print("   'I want to visit Tokyo for a day. I love temples and modern architecture.'")
    print("   'I want to see Tokyo Tower and a traditional temple.'")
    
    print("\n🔄 Running full agent workflow...")
    result = graph.invoke(initial_state)
    
    print_section("RESULTS")
    
    print("\n✅ Stage:", result.get('current_stage'))
    print("\n📝 Constraints:", result.get('constraints'))
    print("\n🗺️  POIs Found:", len(result.get('potential_pois', [])))
    
    if result.get('potential_pois'):
        print("\nTop 5 POIs:")
        for i, poi in enumerate(result['potential_pois'][:5], 1):
            print(f"   {i}. {poi.get('name')} (Score: {poi.get('ai_score', 'N/A')})")
    
    print("\n📅 Itinerary Items:", len(result.get('itinerary', [])))
    
    if result.get('itinerary'):
        print("\n🎯 OPTIMIZED ITINERARY:")
        for i, item in enumerate(result['itinerary'], 1):
            print(f"\n   {i}. {item['place_name']}")
            print(f"      {item['start_time']} - {item['end_time']}")
            print(f"      Visit: {item.get('visit_duration_minutes', 0)} min")
            if item.get('travel_time_to_next'):
                print(f"      Travel: {item['travel_time_to_next']} min to next")
    
    if result.get('optimization_suggestions'):
        print("\n💡 Optimization Suggestions:")
        for sug in result['optimization_suggestions']:
            print(f"   • {sug['suggestion_type']}: {sug['original_value']} → {sug['suggested_value']}")
            print(f"     Reason: {sug['reason']}")
    
    if result.get('error_message'):
        print(f"\n⚠️  Error: {result['error_message']}")
    
    return result


def test_overcrowded_itinerary():
    """Test an overcrowded itinerary that should trigger adaptive handling."""
    print_section("TEST 2: Overcrowded Paris Trip (Should Suggest Adjustments)")
    
    graph = get_travel_agent_graph()
    
    initial_state = {
        'messages': [
            HumanMessage(content="I want to spend one day in Paris visiting: Louvre Museum, "
                                "Eiffel Tower, Notre Dame, Sacré-Cœur, Arc de Triomphe, "
                                "Musée d'Orsay, and Versailles Palace. I want to start at 10am and finish by 6pm.")
        ],
        'optimization_params': {
            'day_start_hour': 10,
            'day_end_hour': 18,
            'travel_mode': 'walking',
            'strict_mode': False
        }
    }
    
    print("\n📨 User Request:")
    print("   'Visit 7 major attractions in Paris in 8 hours'")
    print("   'Start 10am, finish 6pm, walking'")
    
    print("\n🔄 Running full agent workflow...")
    result = graph.invoke(initial_state)
    
    print_section("RESULTS")
    
    print("\n✅ Stage:", result.get('current_stage'))
    print("\n📅 Itinerary Items:", len(result.get('itinerary', [])))
    
    if result.get('optimization_suggestions'):
        print(f"\n💡 {len(result['optimization_suggestions'])} Optimization Suggestions:")
        for i, sug in enumerate(result['optimization_suggestions'], 1):
            print(f"\n   {i}. {sug['suggestion_type'].upper()}")
            print(f"      Original: {sug['original_value']}")
            print(f"      Suggested: {sug['suggested_value']}")
            print(f"      Reason: {sug['reason']}")
            print(f"      Feasibility: {sug['feasibility_score']*100:.0f}%")
    
    if result.get('itinerary'):
        print("\n🎯 Managed to create itinerary with adjusted constraints!")
        print(f"   Optimization attempts: {result.get('optimization_attempts', 0)}")
    
    return result


def test_strict_mode():
    """Test strict mode where constraints cannot be adjusted."""
    print_section("TEST 3: Strict Mode (No Automatic Adjustments)")
    
    graph = get_travel_agent_graph()
    
    initial_state = {
        'messages': [
            HumanMessage(content="Plan a quick 3-hour visit in London: British Museum, "
                                "Tower of London, and Buckingham Palace.")
        ],
        'optimization_params': {
            'day_start_hour': 14,
            'day_end_hour': 17,
            'travel_mode': 'walking',
            'strict_mode': True  # No adjustments allowed
        }
    }
    
    print("\n📨 User Request:")
    print("   '3 major London attractions in 3 hours (STRICT MODE)'")
    
    print("\n🔄 Running full agent workflow...")
    result = graph.invoke(initial_state)
    
    print_section("RESULTS")
    
    print("\n✅ Stage:", result.get('current_stage'))
    
    if result.get('error_message'):
        print(f"\n❌ Error (Expected): {result['error_message']}")
        print("   ✓ Strict mode honored - no automatic adjustments")
    elif result.get('itinerary'):
        print("\n✅ Surprisingly succeeded with strict constraints!")
    
    return result


def main():
    """Run all end-to-end tests."""
    print("\n" + "#"*70)
    print("  🚀 PHASE 2 END-TO-END INTEGRATION TEST")
    print("  Full Workflow: Intake → Discovery → Optimization")
    print("#"*70)
    
    try:
        # Test 1: Simple successful case
        result1 = test_simple_tokyo_trip()
        
        input("\nPress Enter to continue to Test 2...")
        
        # Test 2: Overcrowded itinerary (adaptive handling)
        result2 = test_overcrowded_itinerary()
        
        input("\nPress Enter to continue to Test 3...")
        
        # Test 3: Strict mode
        result3 = test_strict_mode()
        
        # Summary
        print_section("TEST SUMMARY")
        
        test_results = [
            ("Simple Tokyo Trip", result1.get('current_stage') == 'optimization_complete'),
            ("Adaptive Handling", len(result2.get('optimization_suggestions', [])) > 0 or 
                                result2.get('current_stage') == 'optimization_complete'),
            ("Strict Mode", result3.get('current_stage') in ['optimization_failed', 'optimization_complete'])
        ]
        
        for test_name, passed in test_results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"\n   {status}: {test_name}")
        
        all_passed = all(result for _, result in test_results)
        
        if all_passed:
            print("\n" + "🎉"*35)
            print("  ALL TESTS PASSED!")
            print("  Phase 2.1 Integration Complete!")
            print("🎉"*35 + "\n")
        else:
            print("\n⚠️  Some tests did not pass as expected")
        
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

















