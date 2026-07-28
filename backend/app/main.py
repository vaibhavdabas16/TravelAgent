"""FastAPI application entry point for the Intelligent Travel Agent."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import router
from app.api.routes_monitoring import router_monitoring

# Configure logging
# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("backend.log", mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("=" * 50)
    logger.info("Starting Intelligent Travel Agent Backend")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Phase: 2.4 - Caching & Performance")
    logger.info("=" * 50)
    
    # Pre-initialize services to catch configuration errors early
    try:
        from app.services.google_maps import get_google_maps_service
        from app.services.gemini import get_gemini_service
        from app.agents.graph import get_travel_agent_graph
        from app.db import init_db, close_db
        from app.services.vector_store import get_vector_store_service
        from app.services.cache import get_cache_service
        
        logger.info("Initializing services...")
        
        # Cache (Phase 2.4)
        try:
            cache = get_cache_service()
            connected = await cache.connect()
            if connected:
                logger.info("✓ Redis cache connected")
            else:
                logger.warning("⚠ Redis unavailable - caching disabled (graceful degradation)")
        except Exception as cache_err:
            logger.warning(f"Cache initialization error: {cache_err}")
            logger.warning("Continuing without cache")
        
        # Database (Phase 2.2)
        try:
            await init_db()
            logger.info("✓ Database initialized")
        except Exception as db_err:
            logger.warning(f"Database initialization failed: {db_err}")
            logger.warning("Continuing without database (some features will be limited)")
        
        # Vector Store (Phase 2.2)
        try:
            vector_store = get_vector_store_service()
            await vector_store.initialize_collection()
            logger.info("✓ Vector store initialized")
        except Exception as vs_err:
            logger.warning(f"Vector store initialization failed: {vs_err}")
            logger.warning("Continuing without vector store (semantic search disabled)")
        
        # Core services
        get_google_maps_service()
        logger.info("✓ Google Maps service initialized")
        
        get_gemini_service()
        logger.info("✓ Gemini service initialized")
        
        get_travel_agent_graph()
        logger.info("✓ Travel agent graph compiled")
        
        logger.info("All services initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        logger.error("Please check your API keys in the .env file")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Intelligent Travel Agent Backend")
    try:
        from app.services.cache import get_cache_service
        cache = get_cache_service()
        await cache.close()
        logger.info("✓ Cache closed")
    except Exception as e:
        logger.warning(f"Cache shutdown warning: {e}")
    
    try:
        await close_db()
        logger.info("✓ Database closed")
    except Exception as e:
        logger.warning(f"Error closing database: {e}")


# Create FastAPI app
app = FastAPI(
    title="Intelligent Travel Agent API",
    description="""
    An AI-powered travel recommendation system that helps users plan their trips.
    
    **Phase 1 Features:**
    - Natural language trip planning
    - AI-powered POI discovery and scoring
    - Google Maps and Gemini integration
    - Real-time recommendations
    
    **Phase 2.1 Features:**
    - OR-Tools itinerary optimization
    - Multi-modal travel (walking, transit, driving)
    - Adaptive constraint handling
    
    **Phase 2.2 Features (Current):**
    - PostgreSQL database persistence
    - Qdrant vector store for semantic search
    - User authentication & trip management
    - State persistence & session resumption
    
    **Coming Soon:**
    - Accommodation search & integration
    - Multi-day trip planning
    - LocalExpert agent with review analysis
    """,
    version="0.2.2 (Phase 2.2)",
    lifespan=lifespan
)


# CORS middleware for frontend integration
# Supports both local development and ngrok tunnels
cors_origins = settings.all_cors_origins
logger.info(f"CORS enabled for origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes
from app.api.routes_v2 import router_v2
from app.api.routes_planning import router as router_planning

app.include_router(router)  # V1 routes (Phase 1)
app.include_router(router_v2)  # V2 routes (Phase 2.2)
app.include_router(router_planning)  # Interactive Planning routes
app.include_router(router_monitoring)  # Monitoring routes (Phase 2.4)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Intelligent Travel Agent API",
        "version": "0.2.4",
        "phase": "2.4",
        "status": "operational",
        "features": {
            "phase_1": ["Trip planning", "POI discovery", "AI scoring"],
            "phase_2_1": ["Itinerary optimization", "Multi-modal travel", "Adaptive constraints"],
            "phase_2_2": ["Database persistence", "Vector search", "Authentication", "State management"]
        },
        "docs": "/docs",
        "health": "/api/v1/health",
        "endpoints": {
            "v1": "/api/v1",
            "v2": "/api/v2"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again.",
            "error_type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower()
    )

