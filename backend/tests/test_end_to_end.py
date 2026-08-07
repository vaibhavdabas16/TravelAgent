import asyncio
import httpx
import logging
import sys
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://127.0.0.1:8000/api"

async def run_robust_test():
    logger.info("Starting Robust End-to-End Test...")
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        # 0. Health Check
        logger.info("0. Checking API Health...")
        try:
            health = await client.get(f"{BASE_URL}/v1/health")
            health.raise_for_status()
            logger.info(f"✓ API is healthy: {health.json()}")
        except Exception as e:
            logger.error(f"API Health check failed: {e}")
            return

        # 1. Login (to get token)
        logger.info("\n1. Logging in...")
        try:
            login_res = await client.post(f"{BASE_URL}/v2/auth/login", json={
                "email": "test_script@example.com",
                "password": "password123"
            })
            
            if login_res.status_code == 401:
                # Try registering if login fails
                logger.info("Login failed, trying to register...")
                reg_res = await client.post(f"{BASE_URL}/v2/auth/register", json={
                    "email": "test_script@example.com",
                    "password": "password123",
                    "full_name": "Test Script User"
                })
                reg_res.raise_for_status()
                token = reg_res.json()["access_token"]
            else:
                login_res.raise_for_status()
                token = login_res.json()["access_token"]
                
            headers = {"Authorization": f"Bearer {token}"}
            logger.info("✓ Login successful")
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return

        # 2. Create Trip
        logger.info("\n2. Creating Trip (triggers Agent Graph)...")
        user_message = "I want to go to London for 5 days. I love history and pubs. Budget is moderate."
        
        try:
            start_time = time.time()
            create_res = await client.post(
                f"{BASE_URL}/v1/trips", 
                json={"user_message": user_message},
                headers=headers
            )
            create_res.raise_for_status()
            trip_data = create_res.json()
            trip_id = trip_data["trip_id"]
            duration = time.time() - start_time
            
            logger.info(f"✓ Trip created in {duration:.2f}s! ID: {trip_id}")
            
            # Assertions
            assert trip_id, "Trip ID is missing"
            assert trip_data['pois_found'] > 0, f"No POIs found! Got {trip_data['pois_found']}"
            logger.info(f"  Assertion Passed: Found {trip_data['pois_found']} POIs")
            
        except AssertionError as e:
            logger.error(f"Assertion Failed: {e}")
            return
        except Exception as e:
            logger.error(f"Create Trip failed: {e}")
            return

        # 3. Get Trip POIs
        logger.info(f"\n3. Fetching POIs for trip {trip_id}...")
        try:
            pois_res = await client.get(f"{BASE_URL}/v1/trips/{trip_id}/pois", headers=headers)
            pois_res.raise_for_status()
            pois_data = pois_res.json()
            
            # Assertions
            assert len(pois_data['pois']) > 0, "POIs list is empty"
            first_poi = pois_data['pois'][0]
            assert 'ai_score' in first_poi, "POI missing ai_score"
            assert 'score_breakdown' in first_poi, "POI missing score_breakdown"
            
            logger.info(f"✓ Fetched {len(pois_data['pois'])} POIs")
            logger.info(f"  Sample POI: {first_poi['name']} (Score: {first_poi['ai_score']})")
            
        except AssertionError as e:
            logger.error(f"POI Assertion Failed: {e}")
            return
        except Exception as e:
            logger.error(f"Get POIs failed: {e}")
            return

        # 4. Get Full Trip Details (V2)
        logger.info(f"\n4. Fetching full trip details (V2) for {trip_id}...")
        try:
            trip_res = await client.get(f"{BASE_URL}/v2/trips/{trip_id}", headers=headers)
            trip_res.raise_for_status()
            full_trip = trip_res.json()
            
            logger.info("✓ Full trip details fetched")
            constraints = full_trip.get('constraints', {})
            
            # Check for Phase 2 data
            hotels = constraints.get('recommended_hotels', [])
            flights = constraints.get('recommended_flights', [])
            transport = constraints.get('local_transport', {})
            
            # Assertions
            if len(hotels) == 0:
                logger.warning("⚠️ No hotels found (might be expected if API fails, but check logs)")
            else:
                logger.info(f"  Assertion Passed: Found {len(hotels)} hotels")
                
            if len(flights) == 0:
                logger.warning("⚠️ No flights found (might be expected if origin not set)")
            else:
                logger.info(f"  Assertion Passed: Found {len(flights)} flights")
                
            assert transport, "Local transport analysis missing"
            logger.info(f"  Assertion Passed: Local Transport analyzed ({transport.get('recommended_mode')})")
            
        except AssertionError as e:
            logger.error(f"Full Trip Assertion Failed: {e}")
            return
        except Exception as e:
            logger.error(f"Get Full Trip failed: {e}")
            return

    logger.info("\n✓ ROBUST TEST COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_robust_test())
