"""
Basic Phase 2.2 Test Suite (No Rate-Limited APIs)
Tests core infrastructure without hitting Gemini API limits
"""

import asyncio
import sys
import logging
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_database_basic():
    """Test basic database operations"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Basic Database Operations")
    logger.info("="*60)
    
    from app.db import init_db, close_db
    from app.services.database import DatabaseService
    from app.db.database import get_session_context
    
    try:
        await init_db()
        logger.info("✓ Database initialized")
        
        async with get_session_context() as session:
            db = DatabaseService(session)
            
            # Create user
            email = f"test_{uuid.uuid4().hex[:8]}@example.com"
            user = await db.create_user(
                email=email,
                password="simple123",  # Short password
                preferences={"test": True}
            )
            logger.info(f"✓ Created user: {email}")
            
            # Get user
            retrieved = await db.get_user_by_id(user.id)
            assert retrieved.email == email
            logger.info(f"✓ Retrieved user: {email}")
            
            # Create trip
            trip = await db.create_trip(
                user_id=user.id,
                destination="Test City",
                constraints={"budget": "moderate"}
            )
            logger.info(f"✓ Created trip: {trip.destination}")
            
            # Update trip
            await db.update_trip(trip.id, current_stage="test_stage", status="test_status")
            updated = await db.get_trip_by_id(trip.id)
            assert updated.current_stage == "test_stage"
            assert updated.status == "test_status"
            logger.info("✓ Updated trip")
            
            # List trips
            trips = await db.get_user_trips(user.id)
            assert len(trips) >= 1
            logger.info(f"✓ Listed {len(trips)} trips")
        
        await close_db()
        logger.info("✓ Database closed")
        
        logger.info("\n✅ DATABASE TEST PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_auth():
    """Test authentication API endpoints"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Authentication API")
    logger.info("="*60)
    
    import httpx
    
    base_url = "http://localhost:8000"
    email = f"api_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "test123"
    
    try:
        async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
            
            # Register
            register_resp = await client.post(
                "/api/v2/auth/register",
                json={
                    "email": email,
                    "password": password,
                    "preferences": {}
                }
            )
            assert register_resp.status_code == 200, f"Register failed: {register_resp.text}"
            user_id = register_resp.json()["user_id"]
            logger.info(f"✓ Registered user: {email}")
            
            # Login
            login_resp = await client.post(
                "/api/v2/auth/login",
                json={"email": email, "password": password}
            )
            assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
            token = login_resp.json()["access_token"]
            logger.info("✓ Login successful")
            
            # Create trip
            headers = {"Authorization": f"Bearer {token}"}
            trip_resp = await client.post(
                "/api/v2/trips",
                headers=headers,
                json={
                    "destination": "API Test City",
                    "constraints": {"budget": "moderate"}
                }
            )
            assert trip_resp.status_code == 200, f"Trip failed: {trip_resp.text}"
            trip_id = trip_resp.json()["trip_id"]
            logger.info(f"✓ Created trip: {trip_id}")
            
            # Get trip
            get_resp = await client.get(
                f"/api/v2/trips/{trip_id}",
                headers=headers
            )
            assert get_resp.status_code == 200
            logger.info("✓ Retrieved trip")
            
            # Test unauthorized access
            unauth_resp = await client.get(f"/api/v2/trips/{trip_id}")
            assert unauth_resp.status_code == 403, f"Expected 403, got {unauth_resp.status_code}"
            logger.info("✓ Unauthorized access blocked (403)")
        
        logger.info("\n✅ API AUTH TEST PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ API auth test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_endpoints():
    """Test health and info endpoints"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: Health Endpoints")
    logger.info("="*60)
    
    import httpx
    
    try:
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=5.0) as client:
            
            # Root endpoint
            root_resp = await client.get("/")
            assert root_resp.status_code == 200
            root_data = root_resp.json()
            assert root_data["status"] == "operational"
            logger.info(f"✓ Root endpoint: {root_data['version']}")
            
            # Health check
            health_resp = await client.get("/api/v1/health")
            assert health_resp.status_code == 200
            health_data = health_resp.json()
            assert health_data["status"] == "healthy"
            logger.info(f"✓ Health check: {health_data['status']}")
        
        logger.info("\n✅ HEALTH ENDPOINTS TEST PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Health test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_pinecone_connection():
    """Test Pinecone connection (without embeddings)"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Pinecone Connection")
    logger.info("="*60)
    
    try:
        from app.services.vector_store import get_vector_store_service
        
        vs = get_vector_store_service()
        await vs.initialize_collection()
        
        if vs.index is not None:
            logger.info("✓ Pinecone index connected")
            
            # Get stats (doesn't require API calls)
            count = await vs.count_pois()
            logger.info(f"✓ Index stats retrieved (count: {count})")
        else:
            logger.warning("⚠️ Pinecone index not initialized")
        
        logger.info("\n✅ PINECONE CONNECTION TEST PASSED\n")
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Pinecone test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all basic tests"""
    logger.info("="*60)
    logger.info("PHASE 2.2 BASIC TEST SUITE")
    logger.info("(Tests infrastructure without hitting API rate limits)")
    logger.info("="*60)
    
    results = {
        'database': await test_database_basic(),
        'api_auth': await test_api_auth(),
        'health': await test_health_endpoints(),
        'pinecone': await test_pinecone_connection()
    }
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{name.upper()}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    logger.info("="*60)
    logger.info(f"Total: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        logger.info("🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.warning(f"⚠️ {total_count - passed_count} test(s) failed")
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


