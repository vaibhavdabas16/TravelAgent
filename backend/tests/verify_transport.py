import asyncio
import logging
from datetime import date, timedelta
from app.services.providers.transport.amadeus_flights import get_amadeus_flight_provider
from app.services.providers.transport.google_routes import get_google_routes_provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_transport():
    print("=" * 50)
    print("VERIFYING TRANSPORT PROVIDERS")
    print("=" * 50)
    
    # 1. Verify Amadeus Flights
    print("\n✈️  Verifying Amadeus Flight Provider...")
    try:
        flight_provider = get_amadeus_flight_provider()
        
        origin = "JFK"
        destination = "LHR"
        departure = date.today() + timedelta(days=30)
        
        print(f"Searching flights: {origin} -> {destination} on {departure}")
        
        flights = await flight_provider.search(
            origin=origin,
            destination=destination,
            departure_date=departure,
            num_passengers=1,
            filters={"max_results": 3}
        )
        
        if flights:
            print(f"✅ Success! Found {len(flights)} flights:")
            for i, flight in enumerate(flights, 1):
                print(f"{i}. {flight.airline} - ${flight.price}")
                print(f"   Duration: {flight.duration_minutes} min")
                print(f"   Stops: {flight.stops}")
        else:
            print("⚠️ No flights found (check API key or availability)")
            
    except Exception as e:
        print(f"❌ Flight verification failed: {e}")
        import traceback
        traceback.print_exc()

    # 2. Verify Google Routes
    print("\n🗺️  Verifying Google Routes Provider...")
    try:
        route_provider = get_google_routes_provider()
        
        # Times Square to Central Park
        origin = {"lat": 40.7580, "lng": -73.9855}
        destination = {"lat": 40.7829, "lng": -73.9654}
        
        print(f"Calculating route: Times Square -> Central Park (Transit)")
        
        route = await route_provider.get_route(
            origin=origin,
            destination=destination,
            mode="transit"
        )
        
        if route:
            print(f"✅ Success! Found route:")
            print(f"   Duration: {route.duration_seconds // 60} min")
            print(f"   Distance: {route.distance_meters} meters")
            print(f"   Steps: {len(route.steps)}")
            if route.fare:
                print(f"   Fare: {route.fare['amount']} {route.fare['currency']}")
        else:
            print("⚠️ No route found (check API key or location)")
            
    except Exception as e:
        print(f"❌ Route verification failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_transport())
