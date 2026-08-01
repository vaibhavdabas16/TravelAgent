"""Integration tests for the Intelligent Travel Agent.

These tests make real API calls to verify functionality.
Run with: pytest tests/test_integration.py -v

Note: Requires valid API keys in .env file
"""
import pytest
from fastapi.testclient import TestClient

# Import the app
from app.main import app
from app.services.google_maps import get_google_maps_service
from app.services.gemini import get_gemini_service
from app.agents.intake import extract_constraints
from app.tools.geocoding import geocode_location
from app.tools.places import discover_places
from app.tools.scoring import score_poi

# Create test client
client = TestClient(app)


# === Service Tests ===

def test_google_maps_geocoding():
    """Test Google Maps geocoding service."""
    service = get_google_maps_service()
    
    # Test a well-known location
    result = service.geocode("Eiffel Tower, Paris")
    
    assert result is not None
    assert 'lat' in result
    assert 'lng' in result
    assert 'formatted_address' in result
    assert 48.8 < result['lat'] < 48.9  # Approximate Eiffel Tower coordinates
    assert 2.2 < result['lng'] < 2.4
    
    print(f"✓ Geocoding works: {result}")


def test_google_maps_nearby_search():
    """Test Google Maps nearby places search."""
    service = get_google_maps_service()
    
    # Search for cafes near Eiffel Tower
    location = {"lat": 48.8584, "lng": 2.2945}
    places = service.nearby_search(location, 1000, "cafe")
    
    assert places is not None
    assert len(places) > 0
    assert 'name' in places[0]
    assert 'place_id' in places[0]
    
    print(f"✓ Found {len(places)} cafes near Eiffel Tower")


def test_google_maps_place_details():
    """Test Google Maps place details."""
    service = get_google_maps_service()
    
    # First find a place
    places = service.nearby_search({"lat": 48.8584, "lng": 2.2945}, 1000, "restaurant")
    assert len(places) > 0
    
    place_id = places[0]['place_id']
    details = service.place_details(place_id)
    
    assert details is not None
    assert 'name' in details
    
    print(f"✓ Retrieved details for: {details.get('name')}")


def test_gemini_generation():
    """Test Gemini text generation."""
    service = get_gemini_service()
    
    response = service.generate(
        "List 3 famous landmarks in Tokyo. Be brief.",
        temperature=0.2
    )
    
    assert response is not None
    assert len(response) > 10
    assert any(word in response.lower() for word in ['tokyo', 'tower', 'temple', 'shrine', 'palace'])
    
    print(f"✓ Gemini response: {response[:100]}...")


def test_gemini_structured_output():
    """Test Gemini structured JSON output."""
    service = get_gemini_service()
    
    prompt = """Extract as JSON:
    User: "I want to visit Rome for 3 days"
    Return only: {"destination": "...", "duration_days": ...}"""
    
    result = service.generate_structured(prompt, temperature=0.1)
    
    assert isinstance(result, dict)
    assert 'destination' in result
    assert 'Rome' in result['destination']
    
    print(f"✓ Structured output: {result}")


# === Tool Tests ===

def test_geocoding_tool():
    """Test geocoding LangGraph tool."""
    result = geocode_location.invoke({"location": "Barcelona, Spain"})
    
    assert result is not None
    assert 'lat' in result
    assert 'lng' in result
    assert 41.3 < result['lat'] < 41.5
    
    print(f"✓ Geocoded Barcelona: {result}")


def test_places_discovery_tool():
    """Test places discovery tool."""
    pois = discover_places.invoke({
        "location": "Rome, Italy",
        "place_type": "museum",
        "radius_meters": 3000
    })
    
    assert pois is not None
    assert len(pois) > 0
    assert 'place_id' in pois[0]
    assert 'name' in pois[0]
    
    print(f"✓ Discovered {len(pois)} museums in Rome")
    print(f"  Top result: {pois[0]['name']}")


def test_scoring_tool():
    """Test POI scoring tool."""
    # Create a mock POI
    poi = {
        "name": "Test Museum",
        "rating": 4.5,
        "user_ratings_total": 1000,
        "price_level": 2
    }
    
    constraints = {"budget": "moderate"}
    
    scored = score_poi.invoke({"poi": poi, "user_constraints": constraints})
    
    assert 'ai_score' in scored
    assert 'score_breakdown' in scored
    assert 'recommendation_reason' in scored
    assert 0 <= scored['ai_score'] <= 100
    
    print(f"✓ Scored POI: {scored['name']} = {scored['ai_score']}")
    print(f"  Breakdown: {scored['score_breakdown']}")


# === Agent Tests ===

def test_intake_agent():
    """Test the Intake Agent constraint extraction."""
    message = "I want to visit Tokyo for a week in March, interested in temples and sushi, traveling with my wife"
    
    constraints = extract_constraints(message)
    
    assert constraints is not None
    assert constraints['destination'] is not None
    assert 'Tokyo' in constraints['destination']
    assert constraints['num_people'] == 2
    assert 'cultural' in constraints.get('vibe', '').lower() or 'traditional' in constraints.get('vibe', '').lower()
    
    print(f"✓ Extracted constraints: {constraints}")


# === API Endpoint Tests ===

def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert 'status' in data
    assert 'services' in data
    
    print(f"✓ Health check: {data['status']}")
    print(f"  Services: {data['services']}")


def test_create_trip_endpoint():
    """Test creating a trip via API."""
    request_data = {
        "user_message": "I want to visit Paris for 5 days, love art museums and French food, budget is moderate"
    }
    
    response = client.post("/api/v1/trips", json=request_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'trip_id' in data
    assert 'constraints' in data
    assert 'pois_found' in data
    assert data['pois_found'] > 0
    
    trip_id = data['trip_id']
    destination = data['constraints'].get('destination')
    
    print(f"✓ Created trip: {trip_id}")
    print(f"  Destination: {destination}")
    print(f"  POIs found: {data['pois_found']}")
    
    return trip_id


def test_get_trip_pois_endpoint():
    """Test retrieving POIs for a trip."""
    # First create a trip
    trip_id = test_create_trip_endpoint()
    
    # Get POIs
    response = client.get(f"/api/v1/trips/{trip_id}/pois")
    
    assert response.status_code == 200
    data = response.json()
    
    assert 'pois' in data
    assert len(data['pois']) > 0
    
    # Check POI structure
    first_poi = data['pois'][0]
    assert 'place_id' in first_poi
    assert 'name' in first_poi
    assert 'ai_score' in first_poi
    assert 'score_breakdown' in first_poi
    assert 'why_recommended' in first_poi
    
    print(f"✓ Retrieved {len(data['pois'])} POIs for trip")
    print(f"  Top POI: {first_poi['name']} (score: {first_poi['ai_score']})")
    print(f"  Reason: {first_poi['why_recommended']}")


# === End-to-End Scenario Tests ===

@pytest.mark.parametrize("scenario", [
    {
        "input": "I want to visit London for a weekend, love history and museums, budget friendly",
        "expected_destination": "London",
        "min_pois": 5
    },
    {
        "input": "Planning a family trip to Tokyo, 5 days with kids aged 8 and 10",
        "expected_destination": "Tokyo",
        "min_pois": 5
    },
    {
        "input": "Barcelona for 4 days, want beaches and Gaudi architecture, moderate budget",
        "expected_destination": "Barcelona",
        "min_pois": 5
    }
])
def test_end_to_end_scenario(scenario):
    """Test complete end-to-end scenarios."""
    # Create trip
    response = client.post("/api/v1/trips", json={"user_message": scenario["input"]})
    
    assert response.status_code == 200
    data = response.json()
    trip_id = data['trip_id']
    
    # Verify constraints extraction
    assert scenario["expected_destination"].lower() in data['constraints']['destination'].lower()
    
    # Get POIs
    response = client.get(f"/api/v1/trips/{trip_id}/pois")
    assert response.status_code == 200
    
    pois = response.json()['pois']
    assert len(pois) >= scenario["min_pois"]
    
    # Verify all POIs have scores
    for poi in pois:
        assert poi['ai_score'] > 0
        assert 'score_breakdown' in poi
        assert poi['why_recommended'] != ""
    
    # Verify sorting (highest score first)
    scores = [poi['ai_score'] for poi in pois]
    assert scores == sorted(scores, reverse=True)
    
    print(f"✓ Scenario passed: {scenario['input'][:50]}...")
    print(f"  Found {len(pois)} POIs, top: {pois[0]['name']} (score: {pois[0]['ai_score']})")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])






