# ⚙️ Intelligent Travel Agent — Backend Documentation

FastAPI backend service powering the multi-agent travel engine built with **LangGraph**, **Google OR-Tools**, **Google Gemini**, **PostgreSQL**, **Redis** (optional), **Google Maps Platform** (or the free Foursquare + Geoapify alternative), **searchapi.io** and **Pinecone**.

For how the pieces fit together, see [How It Works](../docs/HOW_IT_WORKS.md) and [ARCHITECTURE.md](../ARCHITECTURE.md).

---

## 📋 Directory Architecture

```
backend/
├── alembic/                         # Database migrations (Alembic)
│   ├── env.py
│   └── versions/                    # 001_initial_schema.py, 002_saved_trips.py
├── app/
│   ├── main.py                      # FastAPI app: startup (cache, DB, vector store), CORS, routers
│   ├── config.py                    # Pydantic settings — every environment variable
│   ├── agents/
│   │   ├── graph.py                 # LangGraph StateGraph: intake/discovery nodes + conditional routing
│   │   ├── intake.py                # Gemini constraint extraction and refinement
│   │   ├── discovery.py             # Place search, Gemini relevance filter, must-see boost, top 30
│   │   ├── optimizer.py             # OR-Tools node with constraint-relaxation retries
│   │   ├── accommodation.py         # Hotel search via places provider, location/price scoring
│   │   ├── transport.py             # Flights via searchapi.io, local routes via routing provider
│   │   ├── itinerary.py             # Step-by-step planner: Gemini groups picks into days (SSE stages)
│   │   └── query_generator.py       # Gemini search queries for dining/activities/shopping/wellness
│   ├── api/
│   │   ├── routes.py                # /api/v1: one-shot trips + health
│   │   ├── routes_v2.py             # /api/v2: auth, users, one-shot trips, state, semantic search
│   │   ├── routes_planning.py       # /api/v2/planning: step-by-step planner (in-memory sessions)
│   │   ├── routes_saved_trips.py    # /api/v2/saved-trips: "My trips", scoped to the caller
│   │   ├── routes_monitoring.py     # /api/monitoring: cache, cost, rate-limit, system health
│   │   └── deps.py                  # Auth dependencies (JWT user or guest)
│   ├── db/
│   │   ├── database.py              # Async SQLAlchemy engine and sessions
│   │   └── models.py                # User, Trip, POI, TripPOI, ItineraryItem, SavedTrip
│   ├── models/
│   │   ├── schemas.py               # Pydantic request/response models
│   │   └── state.py                 # TravelAgentState TypedDict
│   ├── services/
│   │   ├── cache.py                 # Redis cache (geocoding + routes in use)
│   │   ├── cost_tracker.py          # Per-user / per-trip API call and cost counters (Redis)
│   │   ├── rate_limiter.py          # Redis rate limiter (implemented, not yet enforced)
│   │   ├── database.py              # User and trip CRUD, bcrypt password hashing
│   │   ├── state_persistence.py     # Saves one-shot graph results to PostgreSQL
│   │   ├── gemini.py                # Gemini 2.5 Flash wrapper with key rotation
│   │   ├── google_maps.py           # Google geocoding/places service + MAPS_PROVIDER factory
│   │   ├── places_foursquare.py     # Foursquare places + Geoapify geocoding
│   │   ├── search_api.py            # searchapi.io client (Google Flights, web search)
│   │   ├── vector_store.py          # Pinecone index + Gemini embeddings (768 dims)
│   │   ├── optimizer.py             # OR-Tools VRPTW model
│   │   ├── price_comparison.py      # Amadeus + SerpAPI hotel prices (not wired into the planner)
│   │   └── providers/
│   │       ├── base.py              # Provider interfaces and Hotel / Flight / Route types
│   │       ├── accommodation/       # google_places.py (used), amadeus.py, serpapi.py
│   │       └── transport/           # google_routes.py, geoapify_routes.py (used), amadeus_flights.py
│   └── tools/                       # LangChain tool wrappers
│       ├── geocoding.py
│       ├── optimizer.py
│       ├── places.py
│       ├── scoring.py
│       └── semantic_search.py
├── tests/                           # 22 test modules (most call live providers)
├── alembic.ini
├── Dockerfile                       # Python 3.12 multi-stage image; runs migrations, then Uvicorn
├── env.example                      # Annotated environment template
├── interactive_demo.py              # Manual demo script
├── quick_test.py                    # Manual smoke-test script
├── start.ps1                        # Windows start helper
└── requirements.txt
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

# Install dependencies
pip install -r requirements.txt
```

### **2. Environment Variables File (`backend/.env`)**
`env.example` is the annotated source of truth for every variable name — copy it rather than retyping, since names must match `app/config.py` exactly:

```bash
cp env.example .env   # then fill in your keys
```

Key points that aren't obvious from the names alone:
- `MAPS_PROVIDER` selects `google` (needs `GOOGLE_MAPS_API_KEY`, billing enabled) or `foursquare` (needs `FOURSQUARE_API_KEY` + `GEOAPIFY_API_KEY`, no card required). It controls places, hotels and routing.
- `GEMINI_API_KEY` is the only key with no default; the app will not start without it.
- `SEARCH_API_KEY` (searchapi.io) is needed for flight options.
- `AMADEUS_*` and `SERPAPI_API_KEY` are optional: those providers exist but no planner step calls them yet.
- The database connection is built from `DATABASE_HOST` / `PORT` / `NAME` / `USER` / `PASSWORD` — there is no `DATABASE_URL`. The code's default port is **5433**, so set `DATABASE_PORT=5432` for a standard Postgres.
- `REDIS_URL`, when set, wins over `REDIS_HOST` / `REDIS_PORT`; this is how a hosted Redis connection string (Render, Upstash, Railway) is wired in. Redis is optional everywhere — the app runs uncached if it's unreachable at startup.
- SearchApi.io and Gemini accept extra numbered keys (`SEARCH_API_KEY1`..`4`, `GEMINI_API_KEY_1`..`3`) that are pooled for basic key rotation under quota.
- `JWT_SECRET_KEY` falls back to a published placeholder if unset — always set a real value outside local dev. Tokens last 7 days.

---

## 🗄️ Database Setup & Migrations (Alembic)

The backend uses **Alembic** for managing PostgreSQL database migrations.

```bash
# Run database migrations to current head
alembic upgrade head

# Generate a new migration script after modifying app/db/models.py
alembic revision --autogenerate -m "Add new field to trips table"
```

The Docker image runs `alembic upgrade head` automatically before starting Uvicorn.

---

## 📡 REST API Reference

Interactive docs for every endpoint are at `http://localhost:8000/docs` when the server is running.

### **1. Authentication & Users (`/api/v2/auth`, `/api/v2/users`)**
- `POST /api/v2/auth/register` — Registers a new user (`email`, `password`, `full_name`). Returns JWT `access_token`.
- `POST /api/v2/auth/login` — Authenticates user credentials (`email`, `password`). Returns JWT `access_token`.
- `GET /api/v2/users/me` — Current user profile (requires Bearer header).
- `GET /api/v2/users/me/stats` — Statistics for the current user.

### **2. Step-by-Step Planner (`/api/v2/planning`)** — used by the web app
Sessions are kept in server memory: a restart or redeploy ends them. Every endpoint accepts a signed-in user or a guest.
- `POST /api/v2/planning/start` — Creates a planning session from the brief. Returns `session_id`.
- `GET /api/v2/planning/{session_id}` — Session summary, used to restore the planner after a refresh.
- `POST /api/v2/planning/{session_id}/places/discover` — Discovers places for the destination and vibe.
- `POST /api/v2/planning/{session_id}/places/select` — Saves selected place IDs.
- `POST /api/v2/planning/{session_id}/accommodations/search` — Hotels from the places provider, scored on travel time to the selected places, price and rating.
- `POST /api/v2/planning/{session_id}/accommodations/select` — Saves selected hotel IDs (also `/accommodation/select`).
- `POST /api/v2/planning/{session_id}/transport/search` — Flight options (searchapi.io) and local routes.
- `POST /api/v2/planning/{session_id}/transport/select` — Saves selected transport IDs.
- `POST /api/v2/planning/{session_id}/{dining|activities|shopping|wellness}/search` — Gemini-generated queries plus place discovery for that category.
- `POST /api/v2/planning/{session_id}/{dining|activities|shopping|wellness}/select` — Saves selections for that category.
- `POST /api/v2/planning/{session_id}/itinerary/generate` — Builds the day-by-day itinerary: Gemini groups the picks into days and searchapi.io adds local transport details.
- `POST /api/v2/planning/{session_id}/itinerary/stream` — Same as above, with `collect → cluster → transport` stage progress streamed over SSE.
- `GET /api/v2/planning/photos/{reference}` — Fetches a place photo server-side and returns the bytes, so the provider key is never exposed to the client.

### **3. One-Shot Planner (`/api/v1/trips`, `/api/v2/trips`)**
Runs the full LangGraph pipeline (intake → discovery → OR-Tools optimizer → accommodation → transport) in a single request. All endpoints require sign-in.
- `POST /api/v1/trips` — Plan from a natural-language message (requires sign-in).
- `GET /api/v1/trips/{trip_id}`, `GET /api/v1/trips/{trip_id}/pois`, `DELETE /api/v1/trips/{trip_id}`
- `POST /api/v2/trips` — Plan from structured input for the signed-in user; persisted to PostgreSQL.
- `GET /api/v2/trips`, `GET /api/v2/trips/{trip_id}`, `DELETE /api/v2/trips/{trip_id}`
- `POST /api/v2/trips/{trip_id}/save-state`, `GET /api/v2/trips/{trip_id}/load-state` — Save or restore the full graph state.

### **4. Saved Trips (`/api/v2/saved-trips`)**
"My trips" for signed-in users, scoped to the caller by `user_id`. Anonymous users fall back to localStorage on the frontend; on login, locally saved trips are migrated here and the local copies dropped.
- `PUT /api/v2/saved-trips/{session_id}` — Create or replace the saved copy of a finished trip. Idempotent.
- `GET /api/v2/saved-trips` — List this user's saved trips (summary rows), newest first.
- `GET /api/v2/saved-trips/{session_id}` — Return one saved trip in full.
- `DELETE /api/v2/saved-trips/{session_id}` — Remove a saved trip.

### **5. Semantic Search (`/api/v2/pois`)**
- `POST /api/v2/pois/semantic-search` — Natural-language POI search over the Pinecone index.
- `GET /api/v2/pois/stats` — Number of indexed POIs. No planner step writes to the index yet, so it may be empty.

### **6. Monitoring & System Status (`/api/monitoring`)**
- `GET /api/monitoring/cache/stats` — Queries Redis live: memory, key count, hits, misses, hit rate. The reliable "is Redis up" check.
- `GET /api/monitoring/cost/trip/{trip_id}` — Per-trip API call and cost breakdown.
- `GET /api/monitoring/cost/user/daily` — Daily cost usage for the current user.
- `GET /api/monitoring/ratelimit/status` — Rate-limit counters for the current user (the limiter is not enforced on routes yet).
- `GET /api/monitoring/system/health` — Status of cache, cost tracking and rate limiter. Cache status is the flag set at startup, not a live check.

### **7. Health (`/api/v1`)**
- `GET /api/v1/health/live` — Free liveness check; touches no provider. Point container/platform health checks here.
- `GET /api/v1/health` — Calls Gemini and the configured maps provider; use for on-demand dependency verification, not polling.

---

## 🧪 Testing Guide

The test suite in `tests/` covers the optimizer, providers, agents and end-to-end flows. Most tests call the real providers, so they need valid keys in `.env` and use API quota. `test_caching.py` and `test_end_to_end.py` also expect the server to be running on `http://localhost:8000`.

```bash
# Run all tests
pytest tests/ -v

# Run multi-agent graph end-to-end integration test
pytest tests/test_phase2_end_to_end.py -v

# Run OR-Tools optimizer tests
pytest tests/test_optimizer.py -v

# Run provider specific tests
pytest tests/test_google_routes.py -v
pytest tests/test_amadeus_flights.py -v   # needs AMADEUS_* keys
```

---

## ⚡ Execution

Start the server using `uvicorn`:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
