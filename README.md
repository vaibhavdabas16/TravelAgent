# 🌍 Intelligent Travel Agent System

A production-grade, AI-powered multi-agent travel planning platform built with **LangGraph**, **FastAPI**, **React 18 (Vite + TypeScript)**, **Google OR-Tools**, **PostgreSQL**, **Pinecone** and **Redis**.

---

## 📸 Overview & Value Proposition

The Intelligent Travel Agent System transforms free-form natural language prompts or structured preferences into fully optimized, multi-day travel itineraries. Unlike simple LLM wrappers, the system combines:

1. **Autonomous AI Agents (LangGraph)**: Specialized nodes for intent extraction, POI discovery, local expert scoring, accommodation selection, and flight/transit routing.
2. **Operations Research Optimization (Google OR-Tools)**: Solves the Vehicle Routing Problem with Time Windows (VRPTW) to construct realistic daily schedules that honor travel times, visit durations, and opening hours.
3. **Swappable Data Providers**: The agent graph is written against provider interfaces, not vendors. Places and routing run on **either** Google Maps Platform **or** a zero-cost Foursquare + Geoapify stack, selected by a single environment variable — no agent code changes.
4. **Real-Time Travel Inventory**: Live flight and hotel offers via Amadeus and searchapi.io, with Pinecone vector similarity search over discovered POIs.
5. **Streaming Multi-Step UI**: A React 18 frontend that streams planning progress over SSE, with an interactive Leaflet map and day-by-day itinerary.

---

## 🏗️ Repository Architecture

```
TravelAgent/
├── README.md                      <- Primary System Guide & Quickstart (This File)
├── ARCHITECTURE.md                <- Deep Technical Architecture & Multi-Agent Flow Specs
├── docker-compose.yml             <- Local stack: Postgres, Redis, backend, frontend
├── render.yaml                    <- Render blueprint: web service + Postgres + Key Value
├── start_app.bat                  <- Windows Dual-Service Dev Server Launcher
│
├── backend/                       <- FastAPI & LangGraph Python Service
│   ├── app/
│   │   ├── agents/                <- LangGraph nodes (intake, discovery, query_generator,
│   │   │                             accommodation, transport, itinerary, optimizer)
│   │   ├── api/                   <- FastAPI REST routes (v1, v2, planning/SSE, monitoring)
│   │   ├── db/                    <- SQLAlchemy async models & database sessions
│   │   ├── models/                <- Pydantic API schemas & TravelAgentState TypedDict
│   │   ├── services/              <- Gemini, places/routing providers, cache, cost tracker,
│   │   │   └── providers/            vector store, rate limiter
│   │   ├── tools/                 <- Geocoding, places and semantic-search wrappers
│   │   ├── config.py              <- Pydantic settings (all environment variables)
│   │   └── main.py                <- Uvicorn application entrypoint
│   ├── tests/                     <- PyTest integration & unit suite
│   ├── alembic/                   <- Database schema migrations
│   ├── Dockerfile                 <- Multi-stage production image
│   ├── env.example                <- Annotated environment template
│   └── requirements.txt           <- Python dependencies
│
└── frontend/                      <- React 18 + Vite + TypeScript Web Application
    ├── src/
    │   ├── components/
    │   │   ├── landing/           <- Apparatus, MeterStrip, SystemMap (hand-built SVG)
    │   │   ├── planning/          <- StepRail, SelectionStep, TripBrief, TripPrompt, progress
    │   │   ├── trip/              <- ItineraryTimeline, DaySelector, Flight/Hotel cards, MapPanel
    │   │   └── shared/            <- Navbar, Footer, CommandPalette, LoginModal, states
    │   ├── contexts/              <- AuthContext (JWT session, migrates local trips on login)
    │   ├── lib/                   <- Trip model/parser, planning steps & storage, saved-trips, theme, format
    │   ├── routes/                <- HomePage, PlanPage, TripPage, TripsPage
    │   ├── services/              <- api.ts (REST client + SSE stream)
    │   ├── index.css              <- Tailwind v4 layers & component primitives
    │   └── main.tsx               <- React DOM entrypoint
    ├── tokens.css                 <- Design tokens consumed by Tailwind v4 @theme
    ├── vercel.json                <- Vercel SPA rewrites & asset caching
    └── vite.config.ts             <- Vite configuration
```

For complete technical specifications, state graph definitions, and database schemas, refer to [ARCHITECTURE.md](ARCHITECTURE.md).

---

## ✨ System Capabilities

### 🤖 **1. Autonomous Multi-Agent Graph (LangGraph)**
- **Intake Node:** Extracts constraints (destination, dates, travelers, budget, vibe, must-see preferences) from natural language or structured forms.
- **Discovery Node:** Hybrid search across the configured places provider and the Pinecone vector index (768-dim Gemini embeddings), filtered by an LLM validation step (`filter_irrelevant_pois`).
- **Optimizer Node:** Converts candidate POIs into a VRPTW model solved by Google OR-Tools, incorporating distance matrices, opening hours, and adaptive time window relaxation.
- **Accommodation Node:** Searches live hotel offers via Amadeus, scoring on proximity to selected POIs, budget fit, and ratings.
- **Transport Node:** Fetches live flight offers (Amadeus, searchapi.io) and multi-modal local transport routes between day stops.

### 🔄 **2. Provider Abstraction**
`MAPS_PROVIDER` selects the places and routing backend at startup:

| Value | Places | Geocoding & routing | Cost |
| :--- | :--- | :--- | :--- |
| `google` *(default)* | Google Places | Google Routes | Billing account required |
| `foursquare` | Foursquare Places | Geoapify | Free tier, no card |

Both implementations satisfy the same interface and return the same shapes, so the agent graph, tools and API responses are identical either way.

### ⚡ **3. Caching & Cost Tracking**
- **Layer 1 (API Cache):** Redis caching for place details (24h), geocoding (7 days), and routes (5 min).
- **Layer 2 (Session Cache):** Trip state persistence in Redis.
- **Layer 3 (LLM Cache):** Deterministic LLM response caching (30 days).
- **Cost Tracker:** Monitors Gemini and external API spend against quota limits.

Redis is **optional everywhere** — if it is unreachable the app logs a warning and runs uncached.

### 🎨 **4. React 18 Web App**
- **Landing page:** Hand-built SVG system map and apparatus diagrams showing the actual planning pipeline.
- **Planning flow:** A step rail over selection steps, with progress streamed live from the backend over SSE.
- **Itinerary view:** Day selector over a timeline, with flight, hotel, local transport and Leaflet map panels.
- **Theming:** Tailwind v4 `@theme` driven by `tokens.css`, with a light/dark toggle.

### 💾 **5. Saved Trips Follow the Account**
"My trips" is backed by a `saved_trips` table (`/api/v2/saved-trips`), scoped to the signed-in user — a trip follows the account to another device, and another user's session id reads as missing rather than forbidden. Guests without an account still get "My trips" via a localStorage fallback; on login, any locally saved trips are uploaded to the account and the local copies are dropped.

---

## 🛠️ Quick Start Guide

### **Prerequisites**

**With Docker (recommended):** Docker Engine 24+ with Compose v2. Nothing else — Postgres and Redis come up with the stack.

**Without Docker:**
- **Python:** 3.12 (the image and CI use 3.12; 3.11 works)
- **Node.js:** 18.0.0 or higher
- **PostgreSQL:** 14+
- **Redis:** 6+ (optional, graceful degradation supported)

---

### **0. Docker Quickstart**

```bash
cp backend/env.example backend/.env   # then fill in your API keys
docker compose up --build
```

| Service  | URL                               |
| :------- | :-------------------------------- |
| Frontend | http://localhost:3000             |
| API docs | http://localhost:8000/docs        |
| Postgres | `localhost:5432` (`travel_agent`) |
| Redis    | `localhost:6379`                  |

The backend mounts `./backend` and runs with `--reload`, so edits apply without a rebuild. The frontend is served by nginx from a production build; since Vite inlines `VITE_API_URL` at build time, changing the API URL means rebuilding that image (`docker compose build frontend`).

The remaining sections cover running the services directly on your machine.

---

### **1. Environment Configuration**

`backend/env.example` is the annotated source of truth — copy it rather than retyping. Variable names below match `app/config.py` exactly.

#### **Backend `.env` (`backend/.env`)**
```ini
# --- Maps / places provider ---
# "google" needs billing enabled; "foursquare" runs on free tiers with no card.
MAPS_PROVIDER=foursquare
GOOGLE_MAPS_API_KEY=            # required only when MAPS_PROVIDER=google
FOURSQUARE_API_KEY=             # required only when MAPS_PROVIDER=foursquare
GEOAPIFY_API_KEY=               # required only when MAPS_PROVIDER=foursquare

# --- AI ---
GEMINI_API_KEY=your_gemini_api_key          # aistudio.google.com/apikey
PINECONE_API_KEY=your_pinecone_api_key      # index is created automatically

# --- Travel inventory ---
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_API_SECRET=your_amadeus_api_secret
SEARCH_API_KEY=your_searchapi_io_key        # flights
SERPAPI_API_KEY=your_serpapi_key            # price intelligence

# --- Database ---
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=travel_agent
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres

# --- Cache (optional) ---
# Hosted Redis: set REDIS_URL to the provider's connection string and it wins
# over the host/port pair. Use rediss:// over the public internet.
# REDIS_URL=
REDIS_HOST=localhost
REDIS_PORT=6379

# --- Security ---
JWT_SECRET_KEY=generate_a_long_random_value
```

#### **Frontend `.env` (`frontend/.env`)**
```ini
VITE_API_URL=http://127.0.0.1:8000/api
```

The `/api` suffix is required — the client appends paths directly to this value. The map uses Leaflet with OpenStreetMap tiles, so no frontend map key is needed.

---

### **2. Running Local Dev Servers**

#### **Option A: Automatic Launcher (Windows)**
```cmd
start_app.bat
```

#### **Option B: Manual Terminal Execution**

**Terminal 1 — Backend (FastAPI):**
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate | Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**Terminal 2 — Frontend (Vite + React):**
```bash
cd frontend
npm install
npm run dev
```
- Web app: [http://localhost:5173](http://localhost:5173)

---

## 🚀 Deployment

The frontend deploys to Vercel as a static SPA; the backend needs a container host, because OR-Tools plus the LangGraph stack exceeds serverless bundle limits and the SSE planning stream needs a long-lived connection.

`render.yaml` provisions the whole backend — web service, Postgres and Redis — as one blueprint.

**1. Backend (Render)**
1. Push the branch to GitHub.
2. Render dashboard → **New → Blueprint** → select the repository.
3. Fill in the secrets marked `sync: false`. `DATABASE_*` and `REDIS_URL` are wired automatically from the managed services; `JWT_SECRET_KEY` is generated.
4. Leave `CORS_ORIGINS` blank until the frontend URL exists.

The container's start command runs `alembic upgrade head` before starting Uvicorn, so the schema is always current on deploy — Render's free plan has no separate pre-deploy hook. The upgrade is idempotent; if it fails, it logs and starts anyway (planning still works, persistence doesn't). `docker compose` runs the same step, so a fresh local volume isn't left with an empty database either.

**2. Frontend (Vercel)**
1. Import the repository, set the root directory to `frontend`.
2. Set `VITE_API_URL` to `https://<your-render-service>.onrender.com/api`.
3. Deploy. `vercel.json` handles SPA rewrites and asset caching.

**3. Close the loop**
Set `CORS_ORIGINS` on Render to the Vercel URL and redeploy. A wrong value here appears as browser CORS failures, not server errors.

### Health endpoints

| Path | Cost | Use |
| :--- | :--- | :--- |
| `/api/v1/health/live` | Free — touches no provider | Container and platform health checks |
| `/api/v1/health` | Calls Gemini + the maps provider | On-demand dependency verification |

Point automated checks at `/health/live`. Polling `/health` on an interval will consume free-tier API quota continuously.

### Free-tier notes

- Render free web services sleep after ~15 minutes idle; the first request afterwards pays a cold start while OR-Tools and LangGraph load.
- Free Postgres instances expire — check Render's current terms before relying on one.
- Free Key Value is small and non-persistent, which is correct for a cache but not for anything that must survive a restart.

---

## 🧪 Testing Strategy

Run the complete backend test suite:
```bash
cd backend
pytest tests/ -v
```

Run specific test modules:
```bash
# Multi-agent end-to-end integration test
pytest tests/test_phase2_end_to_end.py -v

# OR-Tools optimizer test
pytest tests/test_optimizer.py -v

# Amadeus Provider test
pytest tests/test_amadeus_flights.py -v
```

---

## 📑 Complete Documentation Links

- 🏛️ [System Architecture & Agent Specs](ARCHITECTURE.md)
- ⚙️ [Backend Service Documentation](backend/README.md)
- 💻 [Frontend Web App Documentation](frontend/README.md)

---

## 📜 License
This project is licensed under the MIT License.
