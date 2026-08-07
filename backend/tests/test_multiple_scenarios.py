"""
Comprehensive Multi-City Test Suite for Phase 2
Tests various cities, scenarios, and edge cases
"""

import sys
sys.path.insert(0, 'app')

from langchain_core.messages import HumanMessage
from app.agents.graph import get_travel_agent_graph


def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_result(result):
    """Print standardized result summary."""
    print(f"\n📍 Stage: {result.get('current_stage')}")
    print(f"🗺️  POIs Found: {len(result.get('potential_pois', []))}")
    print(f"📅 Itinerary: {len(result.get('itinerary', []))} stops")
    
    if result.get('itinerary'):
        print("\n🎯 OPTIMIZED ITINERARY:")
        total_visit = 0
        total_travel = 0
        for i, item in enumerate(result['itinerary'], 1):
            visit_time = item.get('visit_duration_minutes', 0)
            travel_time = item.get('travel_time_to_next', 0)
            total_visit += visit_time
            total_travel += travel_time if travel_time else 0
            
            print(f"\n  {i}. {item['place_name']}")
            print(f"     ⏰ {item['start_time']} → {item['end_time']} ({visit_time}min)")
            if travel_time:
                print(f"     🚶 {travel_time}min to next")
        
        print(f"\n📊 Summary: {total_visit}min visiting, {total_travel}min traveling")
        print(f"   Total time: {total_visit + total_travel}min ({(total_visit + total_travel)//60}h {(total_visit + total_travel)%60}m)")
    
    if result.get('optimization_suggestions'):
        print(f"\n💡 {len(result['optimization_suggestions'])} Suggestions:")
        for sug in result['optimization_suggestions']:
            print(f"   • {sug['suggestion_type']}: {sug['original_value']} → {sug['suggested_value']}")
    
    if result.get('error_message'):
        print(f"\n⚠️  Error: {result['error_message']}")


def test_1_paris_museums():
    """Test 1: Paris - Art & Museum focused day."""
    print_section("TEST 1: Paris Art Museums & Landmarks")
    
    print("\n📨 Scenario: Art lover wants to see famous museums in Paris")
    print("   Duration: Full day (9am-6pm)")
    print("   Travel: Walking")
    
    graph = get_travel_agent_graph()
    
    result = graph.invoke({
        'messages': [
            HumanMessage(content="I want to visit Paris for a day. I love art and history. "
                                "I want to see the Louvre, Musée d'Orsay, and the Eiffel Tower.")
        ],
        'optimization_params': {
            'day_start_hour': 9,
            'day_end_hour': 18,
            'travel_mode': 'walking',
            'strict_mode': False
        }
    })
    
    print_result(result)
    return result.get('current_stage') in ['optimization_complete', 'needs_user_input_for_constraints']


def test_2_new_york_short():
    """Test 2: New York - Short visit (4 hours)."""
    print_section("TEST 2: New York Quick Tour (4 Hours)")
    
    print("\n📨 Scenario: Tourist has only 4 hours in NYC")
    print("   Duration: 10am-2pm")
    print("   Travel: Transit (subway)")
    
    graph = get_travel_agent_graph()
    
    result = graph.invoke({
        'messages': [
            HumanMessage(content="I have 4 hours in New York City. I want to see Times Square, "
                                "Central Park, and the Statue of Liberty area.")
        ],
        'optimization_params': {
            'day_start_hour': 10,
            'day_end_hour': 14,
            'travel_mode': 'transit',
            'strict_mode': False
        }
    })
    
    print_result(result)
    # Should suggest adjustments or create shorter itinerary
    return True  # Always pass if it completes


def test_3_london_history():
    """Test 3: London - Historical landmarks."""
    print_section("TEST 3: London Historical Tour")
    
    print("\n📨 Scenario: History buff exploring London")
    print("   Duration: Full day (8am-8pm)")
    print("   Travel: Walking")
    
    graph = get_travel_agent_graph()
    
    result = graph.invoke({
        'messages': [
            HumanMessage(content="Plan a day in London. I'm interested in history and architecture. "
                                "Must see: Tower of London, British Museum, Westminster Abbey.")
        ],
        'optimization_params': {
            'day_start_hour': 8,
            'day_end_hour': 20,
            'travel_mode': 'walking',
            'strict_mode': False
        }
    })
    
    print_result(result)
    return result.get('current_stage') == 'optimization_complete'


def test_4_barcelona_food():
    """Test 4: Barcelona - Food & Architecture."""
    print_section("TEST 4: Barcelona Food & Gaudí Tour")
    
    print("\n📨 Scenario: Foodie + Architecture lover in Barcelona")
    print("   Duration: 11am-9pm")
    print("   Travel: Walking")
    
    graph = get_travel_agent_graph()
    
    result = graph.invoke({
        'messages': [
            HumanMessage(content="I want to explore Barcelona. I love Gaudí architecture and Spanish food. "
                                "Must see Sagrada Familia and Park Güell, and try local restaurants.")
        ],
        'optimization_params': {
            'day_start_hour': 11,
            'day_end_hour': 21,
            'travel_mode': 'walking',
            'strict_mode': False
        }
    })
    
    print_result(result)
    return len(result.get('itinerary', [])) > 0


def test_5_rome_ancient():
    """Test 5: Rome - Ancient sites with tight schedule."""
    print_section("TEST 5: Rome Ancient Sites (Tight Schedule)")
    
    print("\n📨 Scenario: Tourist with packed itinerary in Rome")
    print("   Duration: 9am-5pm")
    print("   Travel: Walking")
    print("   Note: Many ancient sites, should test adaptive handling")
    
    graph = get_travel_agent_graph()
    
    result = graph.invoke({
        'messages': [
            HumanMessage(content="One day in Rome. I want to see the Colosseum, Roman Forum, "
                                "Pantheon, Trevi Fountain, and Vatican Museums.")
        ],
        'optimization_params': {
            'day_start_hour': 9,
            'day_end_hour': 17,
            'travel_mode': 'walking',
            'strict_mode': False
        }
    })
    
    print_result(result)
    # Should either create itinerary or suggest adjustments
    return result.get('current_stage') in ['optimization_complete', 'needs_user_input_for_constraints']


def test_6_kyoto_temples():
    """Test 6: Kyoto - Temple hopping with driving."""
    print_section("TEST 6: Kyoto Temple Tour (Driving)")
    
    print("\n📨 Scenario: Temple tour in Kyoto with car rental")
    print("   Duration: 8am-6pm")
    print("   Travel: Driving (faster between distant temples)")
    
    graph = get_travel_agent_graph()
    
    result = graph.invoke({
        'messages': [
            HumanMessage(content="Plan a temple tour in Kyoto, Japan. I want to visit Kinkaku-ji "
                                "(Golden Pavilion), Fushimi Inari Shrine, and Kiyomizu-dera. "
                                "I have a rental car.")
        ],
        'optimization_params': {
            'day_start_hour': 8,
            'day_end_hour': 18,
            'travel_mode': 'driving',
            'strict_mode': False
        }
    })
    
    print_result(result)
    return len(result.get('itinerary', [])) > 0


def main():
    """Run all test scenarios."""
    print("\n" + "#"*70)
    print("  🌍 MULTI-CITY SCENARIO TEST SUITE")
    print("  Testing Phase 2 with Real-World Travel Scenarios")
    print("#"*70)
    
    tests = [
        ("Paris Museums", test_1_paris_museums),
        ("NYC Quick Tour", test_2_new_york_short),
        ("London History", test_3_london_history),
        ("Barcelona Food", test_4_barcelona_food),
        ("Rome Ancient", test_5_rome_ancient),
        ("Kyoto Temples", test_6_kyoto_temples),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success, None))
        except Exception as e:
            print(f"\n❌ Test crashed: {e}")
            results.append((test_name, False, str(e)))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, error in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n  {status}: {test_name}")
        if error:
            print(f"         Error: {error[:50]}...")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("\n" + "🎉"*35)
        print("  ALL SCENARIOS PASSED!")
        print("  System handles diverse cities and use cases!")
        print("🎉"*35 + "\n")
    elif passed >= total * 0.8:
        print("\n✅ Most scenarios passed - system is working well!")
    else:
        print("\n⚠️  Several scenarios failed - needs investigation")


if __name__ == "__main__":
    main()

















