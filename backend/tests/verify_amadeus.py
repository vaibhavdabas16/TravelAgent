import asyncio
import logging
from datetime import date, timedelta
from app.services.providers.accommodation.amadeus import get_amadeus_hotel_provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_amadeus():
    print("Verifying Amadeus Hotel Provider...")
    
    try:
        provider = get_amadeus_hotel_provider()
        
        # Test parameters
        destination = "PAR"  # Paris
        checkin = date.today() + timedelta(days=14)
        checkout = checkin + timedelta(days=3)
        guests = 2
        
        print(f"Searching hotels in {destination} for {guests} guests...")
        print(f"Dates: {checkin} to {checkout}")
        
        hotels = await provider.search(
            destination=destination,
            checkin_date=checkin,
            checkout_date=checkout,
            num_guests=guests,
            filters={"max_results": 5, "currency": "USD"}
        )
        
        if hotels:
            print(f"\n✅ Success! Found {len(hotels)} hotels:")
            for i, hotel in enumerate(hotels, 1):
                print(f"{i}. {hotel.name} ({hotel.rating} stars)")
                print(f"   Price: ${hotel.total_price} (${hotel.price_per_night}/night)")
                print(f"   Location: {hotel.latitude}, {hotel.longitude}")
                print(f"   Provider ID: {hotel.provider_id}")
                print("-" * 40)
        else:
            print("\n⚠️ No hotels found (this might be valid if API key is invalid or no availability)")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_amadeus())
