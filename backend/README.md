# ⚙️ Intelligent Travel Agent — Backend Documentation

FastAPI backend service powering the multi-agent travel engine built with **LangGraph**, **Google OR-Tools**, **PostgreSQL**, **Redis**, **Amadeus API**, **Google Maps Platform**, and **Pinecone**.

---

## 📋 Directory Architecture

```
backend/
├── alembic/                         # Database Migration Scripts (Alembic)
│   ├── env.py
│   └── versions/                    # Migration history (e.g. 001_initial_schema.py)
├── app/
│   ├── main.py                      # FastAPI App Setup, CORS & Global Middleware
│   ├── config.py                    # Pydantic BaseSettings & Environment Configuration
│   ├── agents/                      # LangGraph Agent Nodes
│   │   ├── graph.py                 # Compiled StateGraph Workflow & Conditional Routing
│   │   ├── intake.py                # Intent Extraction & Geocoding Node
│   │   ├── discovery.py             # POI Discovery, Vector Search & LLM Validation Node
│   │   ├── optimizer.py             # OR-Tools VRPTW Itinerary Optimization Node
│   │   ├── accommodation.py         # Amadeus Hotel Search & Location Scoring Node
│   │   ├── transport.py             # Amadeus Flight Search & Google Routes Routing Node
│   │   ├── itinerary.py             # Final Itinerary Builder Node
│   │   └── query_generator.py       # Custom Place Query Generator Node
│   ├── api/                         # REST API Route Controllers
│   │   ├── routes.py                # V1 Legacy Endpoint Controllers
│   │   ├── routes_v2.py             # V2 Auth, User & Trip Persistence Endpoints
│   │   ├── routes_planning.py       # V2 Multi-Step Wizard Planning Endpoints
│   │   ├── routes_monitoring.py     # System Health & Cache Statistics Endpoints
│   │   └── deps.py                  # FastAPI Auth & Database Dependencies
│   ├── db/                          # Database Client & ORM
│   │   ├── session.py               # Async SQLAlchemy Engine & Session Generator
│   │   └── models.py                # User, Trip, POI SQLAlchemy ORM Models
│   ├── models/                      # Schemas & State Types
│   │   ├── schemas.py               # Pydantic Request/Response DTOs
│   │   └── state.py                 # TravelAgentState TypedDict
│   ├── services/                    # Integration & Provider Services
│   │   ├── cache.py                 # Redis 3-Layer Caching Service
│   │   ├── cost_tracker.py          # API Token & Cost Usage Monitoring
│   │   ├── database.py              # Trip & User CRUD Data Access Layer
│   │   ├── gemini.py                # LangChain Gemini Flash API Wrapper
│   │   ├── google_maps.py           # Geocoding, Places & Routes API Service
│   │   ├── price_comparison.py      # SerpAPI & Price Intelligence Service
│   │   ├── search_api.py            # Vector Similarity Search Service
│   │   ├── state_persistence.py     # LangGraph Checkpointer / State Persistence
│   │   └── providers/
│   │       ├── base.py              # Abstract Provider Interfaces
│   │       ├── accommodation/       # Amadeus & Google Places Hotel Providers
│   │       └── transport/           # Google Routes & Transit Providers
│   └── tools/                       # LangChain Tool Wrappers
│       ├── geocoding.py
│       ├── optimizer.py
│       ├── places.py
│       └── scoring.py
├── tests/                           # Consolidated PyTest Test Suite
│   ├── test_agents.py
│   ├── test_amadeus_flights.py
│   ├── test_amadeus_integration.py
│   ├── test_caching.py
│   ├── test_complete_integration.py
│   ├── test_end_to_end.py
│   ├── test_google_routes.py
│   ├── test_phase2_end_to_end.py
│   └── test_week5_price_comparison.py
├── alembic.ini                      # Alembic Configuration File
├── main.py                          # Uvicorn Script Entrypoint Wrapper
├── env.example                      # Environment Template File
└── requirements.txt                 # Python Dependencies
```

---

## 🛠️ Environment Configuration & Setup

### **1. Virtual Environment**
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (Cmd):
.\venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Install exact dependencies
pip install -r requirements.txt
```

### **2. Environment Variables File (`backend/.env`)**
Create a `.env` file inside `backend/` by copying `env.example`:

```ini
# --- Core LLM & Maps Credentials ---
GOOGLE_MAPS_API_KEY=AIzaSy...
GEMINI_API_KEY=AIzaSy...

# --- Travel Provider Credentials ---
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
SERPAPI_KEY=your_serpapi_key

# --- Vector Database ---
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=travel-pois

# --- Database & Caching ---
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/travel_db
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# --- Security ---
JWT_SECRET=supersecretjwtkey_change_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

---

## 🗄️ Database Setup & Migrations (Alembic)

The backend uses **Alembic** for managing PostgreSQL database migrations.

```bash
# Run database migrations to current head
alembic upgrade head

# Generate a new migration script after modifying app/db/models.py
alembic revision --autogenerate -m "Add new field to trips table"
```

---

## 📡 REST API Reference

### **1. Authentication & Users (`/api/v2/auth` & `/api/v2/users`)**
- `POST /api/v2/auth/register` — Registers a new user (`email`, `password`, `full_name`). Returns JWT `access_token`.
- `POST /api/v2/auth/login` — Authenticates user credentials (`email`, `password`). Returns JWT `access_token`.
- `GET /api/v2/users/me` — Fetches current user profile (requires Bearer header).

### **2. Interactive Planning Flow (`/api/v2/planning`)**
- `POST /api/v2/planning/start` — Initializes a new planning session with user query/constraints. Returns `session_id`.
- `POST /api/v2/planning/{session_id}/places/discover` — Discovers POIs based on vibe and destination.
- `POST /api/v2/planning/{session_id}/places/select` — Saves user-selected place IDs.
- `POST /api/v2/planning/{session_id}/accommodations/search` — Fetches hotels with commute proximity scores.
- `POST /api/v2/planning/{session_id}/accommodations/select` — Saves user-selected hotel IDs.
- `POST /api/v2/planning/{session_id}/transport/search` — Fetches flight options & local transit calculations.
- `POST /api/v2/planning/{session_id}/transport/select` — Saves user-selected flight/transit IDs.
- `POST /api/v2/planning/{session_id}/dining/search` — Discovers restaurants matching vibe.
- `POST /api/v2/planning/{session_id}/activities/search` — Discovers adventure/cultural activities.
- `POST /api/v2/planning/{session_id}/shopping/search` — Discovers local markets and shopping districts.
- `POST /api/v2/planning/{session_id}/wellness/search` — Discovers spss, parks, and relaxation spots.
- `POST /api/v2/planning/{session_id}/itinerary/generate` — Executes the OR-Tools optimization engine and returns final day-by-day itinerary.

### **3. Monitoring & System Status (`/api/monitoring`)**
- `GET /api/monitoring/health` — Returns system health status and provider connectivity.
- `GET /api/monitoring/cache/stats` — Returns Redis cache hit rates, memory usage, and key counts.

---

## 🧪 Testing Guide

The test suite in `tests/` covers unit tests, provider integration tests, and multi-agent end-to-end flows.

```bash
# Run all tests
pytest tests/ -v

# Run multi-agent graph end-to-end integration test
pytest tests/test_phase2_end_to_end.py -v

# Run OR-Tools optimizer tests
pytest tests/test_optimizer.py -v

# Run provider specific tests
pytest tests/test_amadeus_flights.py -v
pytest tests/test_google_routes.py -v
```

---

## ⚡ Execution

Start the server using `uvicorn`:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
