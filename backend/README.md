# ⚙️ Intelligent Travel Agent — Backend Documentation

FastAPI backend service powering the multi-agent travel engine built with **LangGraph**, **Google OR-Tools**, **PostgreSQL**, **Redis**, **Amadeus API**, **Google Maps Platform** (or the free Foursquare + Geoapify alternative), and **Pinecone**.

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
│   │   ├── routes_saved_trips.py    # "My trips" CRUD, scoped to the caller
│   │   ├── routes_monitoring.py     # System Health & Cache Statistics Endpoints
│   │   └── deps.py                  # FastAPI Auth & Database Dependencies
│   ├── db/                          # Database Client & ORM
│   │   ├── session.py               # Async SQLAlchemy Engine & Session Generator
│   │   └── models.py                # User, Trip, POI, SavedTrip SQLAlchemy ORM Models
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
│   ├── test_amadeus_flights.py
│   ├── test_amadeus_integration.py
│   ├── test_caching.py
│   ├── test_complete_integration.py
│   ├── test_end_to_end.py
│   ├── test_google_routes.py
│   ├── test_optimizer.py
│   ├── test_optimizer_integration.py
│   ├── test_phase2_end_to_end.py
│   ├── test_week4_agents.py
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
`env.example` is the annotated source of truth for every variable name — copy it rather than retyping, since names must match `app/config.py` exactly:

```bash
cp env.example .env   # then fill in your keys
```

Key points that aren't obvious from the names alone:
- `MAPS_PROVIDER` selects `google` (needs `GOOGLE_MAPS_API_KEY`, billing enabled) or `foursquare` (needs `FOURSQUARE_API_KEY` + `GEOAPIFY_API_KEY`, no card required).
- The database connection is built from `DATABASE_HOST` / `PORT` / `NAME` / `USER` / `PASSWORD` — there is no `DATABASE_URL`.
- `REDIS_URL`, when set, wins over `REDIS_HOST` / `REDIS_PORT`; this is how a hosted Redis connection string (Render, Upstash, Railway) is wired in. Redis is optional everywhere — the app runs uncached if it's unreachable.
- SearchApi.io and Gemini accept extra numbered keys (`SEARCH_API_KEY1`..`4`, `GEMINI_API_KEY_1`..`3`) that are pooled for basic key rotation under quota.
- `JWT_SECRET_KEY` falls back to a published placeholder if unset — always set a real value outside local dev.

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
- `POST /api/v2/planning/{session_id}/wellness/search` — Discovers spas, parks, and relaxation spots.
- `POST /api/v2/planning/{session_id}/itinerary/generate` — Executes the OR-Tools optimization engine and returns final day-by-day itinerary.
- `POST /api/v2/planning/{session_id}/itinerary/stream` — Same as above, streamed stage-by-stage over SSE.
- `GET /api/v2/planning/photos/{reference}` — Fetches a place photo server-side and returns the bytes, so the underlying provider key is never exposed to the client.

### **3. Saved Trips (`/api/v2/saved-trips`)**
"My trips" for signed-in users, scoped to the caller by `user_id`. Anonymous users fall back to localStorage on the frontend; on login, locally saved trips are migrated here and the local copies dropped.
- `PUT /api/v2/saved-trips/{session_id}` — Create or replace the saved copy of a finished trip. Idempotent.
- `GET /api/v2/saved-trips` — List this user's saved trips (summary rows), newest first.
- `GET /api/v2/saved-trips/{session_id}` — Return one saved trip in full.
- `DELETE /api/v2/saved-trips/{session_id}` — Remove a saved trip.

### **4. Monitoring & System Status (`/api/monitoring`)**
- `GET /api/monitoring/cache/stats` — Returns Redis cache hit rates, memory usage, and key counts.
- `GET /api/monitoring/cost/trip/{trip_id}` — Per-trip API/LLM cost breakdown.
- `GET /api/monitoring/cost/user/daily` — Daily cost usage for the current user.
- `GET /api/monitoring/ratelimit/status` — Current rate-limit / quota guard status.
- `GET /api/monitoring/system/health` — Aggregate system health and provider connectivity.

### **5. Health (`/api/v1`, outside the versioned resource routes)**
- `GET /api/v1/health/live` — Free liveness check; touches no provider. Point container/platform health checks here.
- `GET /api/v1/health` — Calls Gemini and the configured maps provider; use for on-demand dependency verification, not polling.

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
