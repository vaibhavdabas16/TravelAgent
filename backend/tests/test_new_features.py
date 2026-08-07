import pytest
import logging
from app.agents.query_generator import QueryGenerator
from app.agents.discovery import discovery_agent
from app.agents.itinerary import ItineraryAgent
from app.api.routes_planning import planning_sessions
from fastapi import FastAPI
from httpx import AsyncClient
import uuid

# Create a dummy app for testing routes
app = FastAPI()
from app.api.routes_planning import router
app.include_router(router)

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_shopping_search_flow():
    """Test the end-to-end shopping search flow."""
    destination = "Tokyo, Japan"
    constraints = {
        "destination": destination,
        "tripStyle": "balanced",
        "budget": "moderate"
    }
    
    # 1. Generate Queries
    query_gen = QueryGenerator()
    queries = await query_gen.generate_queries("shopping", destination, constraints)
    assert len(queries) > 0, "Should generate at least one query"
    
    # 2. Discovery
    discovery_constraints = constraints.copy()
    discovery_constraints["search_queries"] = queries
    
    result = await discovery_agent(discovery_constraints)
    
    assert "error_message" not in result or not result["error_message"]
    assert len(result.get("potential_pois", [])) > 0, "Should find shopping POIs"
    
    first_poi = result["potential_pois"][0]
    assert "name" in first_poi
    assert "formatted_address" in first_poi

@pytest.mark.asyncio
async def test_itinerary_generation_flow():
    """Test the itinerary generation with clustering and transport."""
    session_data = {
        "session_id": "test-session",
        "constraints": {
            "destination": "Paris, France",
            "dates": "2025-06-01 to 2025-06-03",
            "tripStyle": "balanced"
        },
        "selections": {
            "pois": [
                {"name": "Eiffel Tower", "location": {"formatted_address": "Champ de Mars, 5 Av. Anatole France, 75007 Paris", "lat": 48.8584, "lng": 2.2945}},
                {"name": "Louvre Museum", "location": {"formatted_address": "Rue de Rivoli, 75001 Paris", "lat": 48.8606, "lng": 2.3376}},
                {"name": "Notre-Dame Cathedral", "location": {"formatted_address": "6 Parvis Notre-Dame - Pl. Jean-Paul-II, 75004 Paris", "lat": 48.8529, "lng": 2.3500}}
            ],
            "dining": [],
            "shopping": []
        }
    }
    
    agent = ItineraryAgent()
    result = await agent.generate_itinerary(session_data)
    
    assert "itinerary" in result
    itinerary = result["itinerary"]
    assert len(itinerary) > 0
    
    day1 = itinerary[0]
    assert "stops" in day1
    assert "transport_legs" in day1
    
    # Check transport legs
    if len(day1["stops"]) > 1:
        assert len(day1["transport_legs"]) == len(day1["stops"]) - 1
        leg = day1["transport_legs"][0]
        assert "mode" in leg
        assert "duration" in leg
        assert "distance_km" in leg

@pytest.mark.asyncio
async def test_transport_selection():
    # Mock session
    session_id = str(uuid.uuid4())
    planning_sessions[session_id] = {
        "user_id": "test_user",
        "created_at": "2024-01-01T00:00:00",
        "initial_request": {},
        "constraints": {"destination": "Paris"},
        "selections": {"transport": None},
        "discovered_data": {
            "transport": {
                "flights": [{"id": "flight1", "price": 100}, {"id": "flight2", "price": 200}],
                "local": {}
            }
        }
    }
    
    # Test selection
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            f"/api/v2/planning/{session_id}/transport/select",
            json={"selected_transport_ids": ["flight1"]}
        )
        
    assert response.status_code == 200
    assert planning_sessions[session_id]["selections"]["transport"][0]["id"] == "flight1"
