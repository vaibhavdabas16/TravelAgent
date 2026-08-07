"""Integration test for Amadeus Hotel API (Phase 2.3).

This script tests the complete workflow:
1. Initialize Amadeus provider
2. Search for hotels in Paris
3. Display results

Prerequisites:
- Set AMADEUS_API_KEY, AMADEUS_API_SECRET, AMADEUS_BASE_URL in .env
- Run: python test_amadeus_integration.py
"""
import asyncio
import sys
import logging
from datetime import date, timedelta

# Add parent directory to path
sys.path.insert(0, '.')

from app.services.providers.accommodation.amadeus import get_amadeus_hotel_provider

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_amadeus_hotel_search():
    """Test Amadeus hotel search with real API."""
    logger.info("\n" + "="*60)
    logger.info("AMADEUS HOTEL API INTEGRATION TEST")
    logger.info("="*60)
    
    try:
        # Initialize provider
        logger.info("\n1️⃣  Initializing Amadeus provider...")
        provider = get_amadeus_hotel_provider()
        logger.info("✅ Provider initialized successfully")
        
        # Test search
        logger.info("\n2️⃣  Searching for hotels in Paris...")
        logger.info("   Destination: PAR (Paris)")
        logger.info("   Check-in: Tomorrow")
        logger.info("   Check-out: In 5 days")
        logger.info("   Guests: 2")
        
        checkin = date.today() + timedelta(days=1)
        checkout = date.today() + timedelta(days=5)
        
        hotels = await provider.search(
            destination="PAR",  # Paris IATA code
            checkin_date=checkin,
            checkout_date=checkout,
            num_guests=2,
            filters={
                'max_results': 10,  # Limit to 10 hotels for testing
                'currency': 'USD'
            }
        )
        
        # Display results
        logger.info(f"\n3️⃣  Search completed!")
        logger.info(f"   Found {len(hotels)} hotels with available offers")
        
        if hotels:
            logger.info("\n📋 Top 5 Results:")
            for i, hotel in enumerate(hotels[:5], 1):
                logger.info(f"\n   {i}. {hotel.name}")
                logger.info(f"      Price: ${hotel.total_price:.2f} total (${hotel.price_per_night:.2f}/night)")
                logger.info(f"      Rating: {hotel.rating or 'N/A'} ⭐")
                logger.info(f"      Location: {hotel.address}")
                logger.info(f"      Amenities: {', '.join(hotel.amenities[:5])}...")
                logger.info(f"      Cancellation: {hotel.cancellation_policy}")
        else:
            logger.warning("\n⚠️  No hotels found. This could mean:")
            logger.warning("   - Using test environment with limited data")
            logger.warning("   - City code 'PAR' not available in test env")
            logger.warning("   - Try using 'LON' (London) or check production env")
        
        logger.info("\n" + "="*60)
        logger.info("✅ TEST COMPLETE")
        logger.info("="*60)
        
        return len(hotels) > 0
        
    except Exception as e:
        logger.error(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_provider_attributes():
    """Test that provider has correct configuration."""
    logger.info("\n" + "="*60)
    logger.info("PROVIDER CONFIGURATION TEST")
    logger.info("="*60)
    
    provider = get_amadeus_hotel_provider()
    
    logger.info(f"\n✓ API Key: {provider.client_id[:10]}..." if provider.client_id else "❌ Missing")
    logger.info(f"✓ API Secret: {provider.client_secret[:10]}..." if provider.client_secret else "❌ Missing")
    logger.info(f"✓ Environment: {provider.client.hostname}")
    logger.info(f"✓ Cache: {'Connected' if provider.cache else 'Not available'}")
    logger.info(f"✓ Cost Tracker: {'Initialized' if provider.cost_tracker else 'Not available'}")
    
    logger.info("\n" + "="*60)


async def main():
    """Run all tests."""
    logger.info("\n🚀 Starting Amadeus Integration Tests...\n")
    
    # Test 1: Configuration
    await test_provider_attributes()
    
    # Test 2: Real API search
    success = await test_amadeus_hotel_search()
    
    # Summary
    logger.info("\n\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    if success:
        logger.info("✅ All tests passed!")
        logger.info("\nNext steps:")
        logger.info("  1. Try different city codes (LON, NYC, TYO)")
        logger.info("  2. Test with different date ranges")
        logger.info("  3. Add filters (ratings, amenities)")
        logger.info("  4. Move to Week 2: Amadeus Flight API")
        return 0
    else:
        logger.warning("⚠️  Tests completed with warnings")
        logger.info("\nTroubleshooting:")
        logger.info("  1. Verify .env has AMADEUS_API_KEY and AMADEUS_API_SECRET")
        logger.info("  2. Check AMADEUS_BASE_URL is set correctly")
        logger.info("  3. Confirm API keys are for test environment")
        logger.info("  4. Try 'LON' instead of 'PAR' (London has more test data)")
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








