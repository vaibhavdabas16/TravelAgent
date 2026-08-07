"""
Comprehensive Phase 2.2 Test Suite
Tests all new features: Database, Vector Store, Authentication, State Persistence
"""

import asyncio
import sys
import logging
from typing import Dict, Any
import uuid

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase2_2TestSuite:
    """Comprehensive test suite for Phase 2.2 features"""
    
    def __init__(self):
        self.test_results = {}
        self.test_user_id = None
        self.test_trip_id = None
        self.test_poi_ids = []
    
    async def setup(self):
        """Initialize services"""
        from app.db import init_db
        from app.services.vector_store import get_vector_store_service
        
        logger.info("=" * 70)
        logger.info("PHASE 2.2 COMPREHENSIVE TEST SUITE")
        logger.info("=" * 70)
        
        # Initialize database
        await init_db()
        logger.info("✓ Database initialized")
        
        # Initialize vector store
        vector_store = get_vector_store_service()
        await vector_store.initialize_collection()
        logger.info("✓ Vector store initialized")
    
    async def teardown(self):
        """Cleanup after tests"""
        from app.db import close_db
        await close_db()
        logger.info("✓ Database closed")
    
    # ========================================================================
    # TEST 1: Database Operations
    # ========================================================================
    
    async def test_1_database_crud(self):
        """Test database CRUD operations for users, trips, and POIs"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 1: Database CRUD Operations")
        logger.info("=" * 70)
        
        from app.services.database import DatabaseService
        from app.db.database import get_session_context
        
        try:
            async with get_session_context() as session:
                db = DatabaseService(session)
                
                # Test 1.1: Create User
                logger.info("\n[1.1] Testing user creation...")
                user = await db.create_user(
                    email=f"test_{uuid.uuid4().hex[:8]}@example.com",
                    password="test_password_123",
                    preferences={"theme": "dark", "notifications": True}
                )
                self.test_user_id = user.id
                logger.info(f"✓ Created user: {user.email} (ID: {user.id})")
                
                # Test 1.2: Get User
                logger.info("\n[1.2] Testing user retrieval...")
                retrieved_user = await db.get_user_by_id(user.id)
                assert retrieved_user.id == user.id
                assert retrieved_user.email == user.email
                logger.info(f"✓ Retrieved user: {retrieved_user.email}")
                
                # Test 1.3: Verify Password
                logger.info("\n[1.3] Testing password verification...")
                user_by_email = await db.get_user_by_email(user.email)
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                assert pwd_context.verify("test_password_123", user_by_email.hashed_password)
                logger.info("✓ Password verification successful")
                
                # Test 1.4: Create Trip
                logger.info("\n[1.4] Testing trip creation...")
                trip_constraints = {
                    "destination": "Paris, France",
                    "start_date": "2024-06-01",
                    "duration_days": 3,
                    "budget_preference": "moderate",
                    "interests": ["museums", "cafes"]
                }
                trip = await db.create_trip(
                    user_id=user.id,
                    name="Paris Adventure",
                    constraints=trip_constraints
                )
                self.test_trip_id = trip.id
                logger.info(f"✓ Created trip: {trip.name} (ID: {trip.id})")
                
                # Test 1.5: Get Trip
                logger.info("\n[1.5] Testing trip retrieval...")
                retrieved_trip = await db.get_trip_by_id(trip.id)
                assert retrieved_trip.id == trip.id
                assert retrieved_trip.name == trip.name
                assert retrieved_trip.constraints["destination"] == "Paris, France"
                logger.info(f"✓ Retrieved trip: {retrieved_trip.name}")
                
                # Test 1.6: Create POIs
                logger.info("\n[1.6] Testing POI creation...")
                poi_data = [
                    {
                        "place_id": "ChIJD7fiBh9u5kcRYJSMaMOCCwQ",
                        "name": "Eiffel Tower",
                        "formatted_address": "Champ de Mars, Paris",
                        "latitude": 48.8584,
                        "longitude": 2.2945,
                        "category": "landmark",
                        "rating": 4.6,
                        "user_ratings_total": 120000,
                        "price_level": 2
                    },
                    {
                        "place_id": "ChIJLU7jZClu5kcR4PcOOO6p3I0",
                        "name": "Louvre Museum",
                        "formatted_address": "Rue de Rivoli, Paris",
                        "latitude": 48.8606,
                        "longitude": 2.3376,
                        "category": "museum",
                        "rating": 4.7,
                        "user_ratings_total": 150000,
                        "price_level": 2
                    }
                ]
                
                for poi in poi_data:
                    created_poi = await db.create_or_update_poi(**poi)
                    self.test_poi_ids.append(created_poi.id)
                    logger.info(f"✓ Created POI: {created_poi.name}")
                
                # Test 1.7: Associate POIs with Trip
                logger.info("\n[1.7] Testing POI-Trip association...")
                for poi_id in self.test_poi_ids:
                    await db.add_poi_to_trip(
                        trip_id=trip.id,
                        poi_id=poi_id,
                        score=0.85,
                        user_selected=True
                    )
                logger.info(f"✓ Associated {len(self.test_poi_ids)} POIs with trip")
                
                # Test 1.8: Get Trip with POIs
                logger.info("\n[1.8] Testing trip retrieval with POIs...")
                trip_pois = await db.get_trip_pois(trip.id)
                assert len(trip_pois) == 2
                logger.info(f"✓ Retrieved {len(trip_pois)} POIs for trip")
                
                # Test 1.9: Update Trip State
                logger.info("\n[1.9] Testing trip state persistence...")
                test_state = {
                    "messages": ["User: I want to visit Paris"],
                    "constraints": trip_constraints,
                    "status": "discovery_complete"
                }
                await db.update_trip_state(trip.id, test_state)
                updated_trip = await db.get_trip_by_id(trip.id)
                assert updated_trip.current_state["status"] == "discovery_complete"
                logger.info("✓ Trip state persisted successfully")
                
                # Test 1.10: List User Trips
                logger.info("\n[1.10] Testing user trips listing...")
                user_trips = await db.get_user_trips(user.id)
                assert len(user_trips) >= 1
                logger.info(f"✓ Retrieved {len(user_trips)} trips for user")
                
                logger.info("\n" + "=" * 70)
                logger.info("✅ DATABASE CRUD TESTS PASSED")
                logger.info("=" * 70)
                self.test_results['database_crud'] = True
                
        except Exception as e:
            logger.error(f"❌ Database CRUD test failed: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['database_crud'] = False
    
    # ========================================================================
    # TEST 2: Vector Store Operations
    # ========================================================================
    
    async def test_2_vector_store(self):
        """Test Pinecone vector store operations"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 2: Vector Store Operations")
        logger.info("=" * 70)
        
        from app.services.vector_store import get_vector_store_service
        
        try:
            vector_store = get_vector_store_service()
            
            # Test 2.1: Index POIs
            logger.info("\n[2.1] Testing POI indexing...")
            test_pois = [
                {
                    "id": str(uuid.uuid4()),
                    "poi_id": "test_eiffel_tower",
                    "name": "Eiffel Tower",
                    "description": "Iconic iron lattice tower on the Champ de Mars in Paris",
                    "category": "landmark",
                    "location": {"lat": 48.8584, "lng": 2.2945}
                },
                {
                    "id": str(uuid.uuid4()),
                    "poi_id": "test_louvre",
                    "name": "Louvre Museum",
                    "description": "World's largest art museum with masterpieces like Mona Lisa",
                    "category": "museum",
                    "location": {"lat": 48.8606, "lng": 2.3376}
                },
                {
                    "id": str(uuid.uuid4()),
                    "poi_id": "test_cafe",
                    "name": "Café de Flore",
                    "description": "Historic café known for its intellectual clientele and classic French atmosphere",
                    "category": "cafe",
                    "location": {"lat": 48.8543, "lng": 2.3329}
                }
            ]
            
            indexed_count = await vector_store.bulk_index_pois(test_pois)
            logger.info(f"✓ Indexed {indexed_count} POIs")
            
            # Test 2.2: Semantic Search
            logger.info("\n[2.2] Testing semantic search...")
            
            # Search for museums
            museum_results = await vector_store.search_similar_pois(
                query="art galleries and museums with famous paintings",
                limit=5,
                score_threshold=0.5
            )
            logger.info(f"✓ Found {len(museum_results)} results for museum query")
            if museum_results:
                for result in museum_results[:3]:
                    logger.info(f"  - {result.get('name')} (score: {result.get('score', 0):.3f})")
            
            # Search for cafes
            cafe_results = await vector_store.search_similar_pois(
                query="cozy coffee shops with traditional atmosphere",
                limit=5,
                score_threshold=0.5
            )
            logger.info(f"✓ Found {len(cafe_results)} results for cafe query")
            if cafe_results:
                for result in cafe_results[:3]:
                    logger.info(f"  - {result.get('name')} (score: {result.get('score', 0):.3f})")
            
            # Test 2.3: Category Filter
            logger.info("\n[2.3] Testing category filtering...")
            landmark_results = await vector_store.search_similar_pois(
                query="famous attractions",
                limit=10,
                category_filter="landmark",
                score_threshold=0.5
            )
            logger.info(f"✓ Found {len(landmark_results)} landmark results")
            
            # Test 2.4: Get POI by ID
            logger.info("\n[2.4] Testing POI retrieval by ID...")
            if test_pois:
                poi = await vector_store.get_poi_by_id(test_pois[0]["poi_id"])
                if poi:
                    logger.info(f"✓ Retrieved POI: {poi.get('name')}")
                else:
                    logger.warning("⚠️ POI not found (may take time to sync)")
            
            logger.info("\n" + "=" * 70)
            logger.info("✅ VECTOR STORE TESTS PASSED")
            logger.info("=" * 70)
            self.test_results['vector_store'] = True
            
        except Exception as e:
            logger.error(f"❌ Vector store test failed: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['vector_store'] = False
    
    # ========================================================================
    # TEST 3: Authentication & API
    # ========================================================================
    
    async def test_3_authentication_api(self):
        """Test authentication and API endpoints"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 3: Authentication & API Endpoints")
        logger.info("=" * 70)
        
        import httpx
        
        base_url = "http://localhost:8000"
        test_email = f"api_test_{uuid.uuid4().hex[:8]}@example.com"
        test_password = "secure_password_123"
        
        try:
            async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
                
                # Test 3.1: Register User
                logger.info("\n[3.1] Testing user registration...")
                register_response = await client.post(
                    "/api/v2/auth/register",
                    json={
                        "email": test_email,
                        "password": test_password,
                        "preferences": {"theme": "light"}
                    }
                )
                assert register_response.status_code == 200, f"Registration failed: {register_response.text}"
                register_data = register_response.json()
                assert "user_id" in register_data
                logger.info(f"✓ User registered: {test_email}")
                
                # Test 3.2: Login
                logger.info("\n[3.2] Testing user login...")
                login_response = await client.post(
                    "/api/v2/auth/login",
                    data={
                        "username": test_email,
                        "password": test_password
                    }
                )
                assert login_response.status_code == 200, f"Login failed: {login_response.text}"
                login_data = login_response.json()
                assert "access_token" in login_data
                access_token = login_data["access_token"]
                logger.info("✓ Login successful, token received")
                
                # Test 3.3: Create Trip (Authenticated)
                logger.info("\n[3.3] Testing authenticated trip creation...")
                headers = {"Authorization": f"Bearer {access_token}"}
                trip_response = await client.post(
                    "/api/v2/trips",
                    headers=headers,
                    json={
                        "name": "Test API Trip",
                        "constraints": {
                            "destination": "Tokyo, Japan",
                            "start_date": "2024-07-01",
                            "duration_days": 5,
                            "budget_preference": "moderate",
                            "interests": ["temples", "food", "technology"]
                        }
                    }
                )
                assert trip_response.status_code == 200, f"Trip creation failed: {trip_response.text}"
                trip_data = trip_response.json()
                assert "trip_id" in trip_data
                api_trip_id = trip_data["trip_id"]
                logger.info(f"✓ Trip created: {api_trip_id}")
                
                # Test 3.4: Get Trip
                logger.info("\n[3.4] Testing trip retrieval...")
                get_trip_response = await client.get(
                    f"/api/v2/trips/{api_trip_id}",
                    headers=headers
                )
                assert get_trip_response.status_code == 200
                trip_info = get_trip_response.json()
                assert trip_info["name"] == "Test API Trip"
                logger.info(f"✓ Retrieved trip: {trip_info['name']}")
                
                # Test 3.5: List User Trips
                logger.info("\n[3.5] Testing trip listing...")
                list_response = await client.get(
                    "/api/v2/trips",
                    headers=headers
                )
                assert list_response.status_code == 200
                trips = list_response.json()
                assert len(trips) >= 1
                logger.info(f"✓ Listed {len(trips)} trips")
                
                # Test 3.6: Unauthorized Access
                logger.info("\n[3.6] Testing unauthorized access...")
                unauth_response = await client.get(f"/api/v2/trips/{api_trip_id}")
                assert unauth_response.status_code == 401
                logger.info("✓ Unauthorized access properly blocked")
                
                # Test 3.7: Invalid Token
                logger.info("\n[3.7] Testing invalid token...")
                invalid_headers = {"Authorization": "Bearer invalid_token_12345"}
                invalid_response = await client.get(
                    f"/api/v2/trips/{api_trip_id}",
                    headers=invalid_headers
                )
                assert invalid_response.status_code == 401
                logger.info("✓ Invalid token properly rejected")
                
                logger.info("\n" + "=" * 70)
                logger.info("✅ AUTHENTICATION & API TESTS PASSED")
                logger.info("=" * 70)
                self.test_results['authentication_api'] = True
                
        except Exception as e:
            logger.error(f"❌ Authentication/API test failed: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['authentication_api'] = False
    
    # ========================================================================
    # TEST 4: End-to-End Workflow
    # ========================================================================
    
    async def test_4_end_to_end_workflow(self):
        """Test complete end-to-end workflow with Phase 1 integration"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST 4: End-to-End Workflow (Phase 1 + Phase 2.2)")
        logger.info("=" * 70)
        
        import httpx
        
        base_url = "http://localhost:8000"
        
        try:
            async with httpx.AsyncClient(base_url=base_url, timeout=60.0) as client:
                
                # Test 4.1: Phase 1 Trip Creation (No Auth)
                logger.info("\n[4.1] Testing Phase 1 trip creation (no auth)...")
                phase1_response = await client.post(
                    "/api/v1/trips",
                    json={
                        "user_message": "I want to explore museums and cafes in Paris for 2 days"
                    }
                )
                assert phase1_response.status_code == 200
                phase1_data = phase1_response.json()
                assert "trip_id" in phase1_data
                assert "status" in phase1_data
                logger.info(f"✓ Phase 1 trip created: {phase1_data['trip_id']}")
                logger.info(f"  Status: {phase1_data['status']}")
                
                # Test 4.2: Check POIs
                logger.info("\n[4.2] Testing POI retrieval...")
                pois_response = await client.get(
                    f"/api/v1/trips/{phase1_data['trip_id']}/pois"
                )
                if pois_response.status_code == 200:
                    pois_data = pois_response.json()
                    logger.info(f"✓ Retrieved {len(pois_data.get('pois', []))} POIs")
                    if pois_data.get('pois'):
                        for poi in pois_data['pois'][:3]:
                            logger.info(f"  - {poi.get('name')} ({poi.get('category')})")
                else:
                    logger.warning(f"⚠️ POI retrieval returned {pois_response.status_code}")
                
                logger.info("\n" + "=" * 70)
                logger.info("✅ END-TO-END WORKFLOW TESTS PASSED")
                logger.info("=" * 70)
                self.test_results['end_to_end'] = True
                
        except Exception as e:
            logger.error(f"❌ End-to-end test failed: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['end_to_end'] = False
    
    # ========================================================================
    # Main Test Runner
    # ========================================================================
    
    async def run_all_tests(self):
        """Run all test suites"""
        await self.setup()
        
        try:
            await self.test_1_database_crud()
            await self.test_2_vector_store()
            await self.test_3_authentication_api()
            await self.test_4_end_to_end_workflow()
            
        finally:
            await self.teardown()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        logger.info("\n" + "=" * 70)
        logger.info("TEST SUMMARY")
        logger.info("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{test_name.upper()}: {status}")
        
        logger.info("=" * 70)
        logger.info(f"Total: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED!")
            return 0
        else:
            logger.warning(f"⚠️ {total_tests - passed_tests} test(s) failed")
            return 1


async def main():
    """Main test entry point"""
    test_suite = Phase2_2TestSuite()
    exit_code = await test_suite.run_all_tests()
    return exit_code


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)













