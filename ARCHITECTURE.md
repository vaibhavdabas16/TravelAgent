# 🏛️ Deep Technical Architecture & Multi-Agent Specifications

This document details the architectural design, multi-agent state graph, optimization algorithms, data models, and caching strategies of the **Intelligent Travel Agent System**.

---

## 🎯 Architecture Overview

The system processes natural language or structured travel queries into an optimized, multi-day itinerary. It combines deterministic optimization (OR-Tools) with non-deterministic intelligence (LangChain/Gemini) orchestrated by a **LangGraph state graph**.

```
                           ┌──────────────────────────┐
                           │   React 18 Frontend UI   │
                           └────────────┬─────────────┘
                                        │ (HTTPS / REST)
                                        ▼
                           ┌──────────────────────────┐
                           │   FastAPI REST Routes    │
                           │     (/v1 & /v2 API)      │
                           └────────────┬─────────────┘
                                        │
                                        ▼
                      ┌────────────────────────────────────┐
                      │    LangGraph State Workflow        │
                      │  TravelAgentState (TypedDict)      │
                      └─────────────────┬──────────────────┘
                                        │
        ┌───────────────────┬───────────┴───────┬───────────────────┐
        ▼                   ▼                   ▼                   ▼
 ┌──────────────┐   ┌──────────────┐   ┌─────────────────┐  ┌──────────────┐
 │ Intake Node  │   │Discovery Node│   │ Optimizer Node  │  │Accom & Trans │
 └──────┬───────┘   └──────┬───────┘   └────────┬────────┘  └──────┬───────┘
        │                  │                    │                  │
        ▼                  ▼                    ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌─────────────────┐  ┌──────────────┐
│Gemini Flash  │   │Google Places │   │ Google OR-Tools │  │ Amadeus API  │
│Constraints   │   │+ Pinecone DB │   │ VRPTW Solver    │  │ + Routes API │
└──────────────┘   └──────────────┘   └─────────────────┘  └──────────────┘
        │                  │                    │                  │
        └──────────────────┴───────────┬────────┴──────────────────┘
                                       │
                                       ▼
                       ┌──────────────────────────────┐
                       │  Persistence & Cache Layer   │
                       │  - Redis 3-Layer Cache       │
                       │  - PostgreSQL DB             │
                       │  - Pinecone 768d Vectors     │
                       └──────────────────────────────┘
```

---

## 🤖 LangGraph Multi-Agent Workflow State Graph

The agent graph is defined in `backend/app/agents/graph.py`. State transitions are governed by the `TravelAgentState` dictionary.

```
                         [ START ]
                             │
                             ▼
                      ┌─────────────┐
                      │ intake_node │
                      └──────┬──────┘
                             │ (intake_complete)
                             ▼
                    ┌──────────────────┐
                    │ discovery_node   │
                    └────────┬─────────┘
                             │ (discovery_complete)
                             ▼
                    ┌──────────────────┐  ◄──┐
                    │  optimizer_node  │     │ (retrying_optimization)
                    └────────┬─────────┘  ───┘
                             │ (optimization_complete / fallback)
                             ▼
                ┌───────────────────────────┐
                │ accommodation_agent_node  │
                └────────────┬──────────────┘
                             │ (accommodation_complete)
                             ▼
                   ┌──────────────────┐
                   │  transport_node  │
                   └─────────┬────────┘
                             │ (transport_complete)
                             ▼
                          [ END ]
```

### **Graph Nodes Specification:**

| Node Name | File Location | Responsible Logic | Output Artifacts |
| :--- | :--- | :--- | :--- |
| **`intake`** | `app/agents/intake.py` | Extracts trip destination, dates, budget, vibe, travelers, amenities, and must-see list. Geocodes destination. | `constraints`, `destination_coords` |
| **`discovery`** | `app/agents/discovery.py` | Hybrid POI search via Google Places & Pinecone vector similarity. Applies LLM quality filtering (`filter_irrelevant_pois`) and must-see score boosting. | `potential_pois` (Top 30 ranked POIs) |
| **`optimizer`** | `app/agents/optimizer.py` | Solves Vehicle Routing Problem with Time Windows (VRPTW) using Google OR-Tools. | `itinerary` (Day-by-day structured stops) |
| **`accommodation`**| `app/agents/accommodation.py` | Searches hotel offers via Amadeus API / SerpAPI. Scores hotels by proximity to itinerary POIs. | `recommended_hotels`, `selected_accommodation` |
| **`transport`** | `app/agents/transport.py` | Searches flight offers (Amadeus) and calculates local Transit/Driving/Walking matrices (Google Routes). | `recommended_flights`, `local_transport` |

---

## 🧮 Operations Research Optimization (OR-Tools VRPTW)

The itinerary optimizer (`backend/app/services/optimizer.py` & `app/agents/optimizer.py`) models travel planning as a **Vehicle Routing Problem with Time Windows (VRPTW)**.

### **Mathematical Formulation:**
- **Nodes ($N$)**: Start depot (hotel/center), end depot, and $n$ candidate POIs.
- **Decision Variable ($x_{ijk}$)**: Binary variable equal to $1$ if vehicle/day $k$ travels directly from POI $i$ to POI $j$.
- **Time Dimension ($T_i$)**: Arrival time at POI $i$.
- **Constraints:**
  1. **Time Window**: $e_i \le T_i \le l_i$, where $e_i$ is opening time and $l_i$ is closing time.
  2. **Service Time**: $T_j \ge T_i + \text{duration}_i + t_{ij}$ where $t_{ij}$ is travel duration from Google Routes API.
  3. **Day Bounds**: Day start hour (default `09:00`) to day end hour (default `22:00`).
  4. **Pace Limit**: Maximum POIs per day based on user preference (Laid-back: 2-3 POIs/day, Balanced: 4-5 POIs/day, Adventurous: 6+ POIs/day).

### **Adaptive Constraint Relaxation Fallback:**
If OR-Tools fails to find a feasible solution within strict bounds:
1. **Attempt 1:** Standard optimization with exact time windows.
2. **Attempt 2 (Automatic Relaxation):** Expands day bounds (e.g. `08:00` to `23:00`) and relaxes non-strict POI closing times by 30 minutes.
3. **Attempt 3 (Greedy Fallback):** Truncates lowest-scoring POIs and re-optimizes core cluster.

---

## 🗄️ Database Schema & Persistence

The application uses **PostgreSQL** via async **SQLAlchemy** (`backend/app/db/models.py`).

### **Entity-Relationship Diagram**

```
 ┌──────────────────────┐         ┌──────────────────────┐
 │        users         │         │        trips         │
 ├──────────────────────┤         ├──────────────────────┤
 │ id (UUID) [PK]       │◄───────┐│ id (UUID) [PK]       │
 │ email (VARCHAR)      │        ││ user_id (UUID) [FK]  │
 │ hashed_password      │        ││ destination (VARCHAR)│
 │ full_name (VARCHAR)  │        ││ status (VARCHAR)     │
 │ created_at (TIMESTAMP)        ││ constraints (JSONB)  │
 └──────────────────────┘        ││ itinerary (JSONB)    │
                                 ││ created_at           │
                                 └──────────────────────┘
                                            │
                                            ▼
                                 ┌──────────────────────┐
                                 │         pois         │
                                 ├──────────────────────┤
                                 │ place_id (STR) [PK]  │
                                 │ name (VARCHAR)       │
                                 │ rating (FLOAT)       │
                                 │ location (GEOMETRY)  │
                                 │ metadata (JSONB)     │
                                 └──────────────────────┘
```

---

## ⚡ Redis 3-Layer Caching Architecture

Caching is managed centrally by `CacheService` (`backend/app/services/cache.py`).

| Layer | Key Pattern | Target Data | TTL | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Layer 1: API Response** | `travel:geocode:{hash}` | Geocoding coordinates | 7 Days (`604,800s`) | Coordinates rarely change |
| **Layer 1: API Response** | `travel:place:{place_id}` | Google Place details & photos | 24 Hours (`86,400s`) | Fresh ratings & hours |
| **Layer 1: API Response** | `travel:route:{hash}` | Travel times & directions | 5 Minutes (`300s`) | Handles live traffic |
| **Layer 2: Session State**| `travel:trip:{id}:state` | Full LangGraph State | Permanent (Manual deletion)| Active user planning session |
| **Layer 3: LLM Response** | `travel:llm:{hash}` | Gemini LLM prompt outputs | 30 Days (`2,592,000s`) | Save token costs |

---

## 💳 Provider Integrations & Cost Tracking

The `CostTracker` service (`backend/app/services/cost_tracker.py`) logs API usage metrics to prevent quota overruns.

| Provider | Purpose | Rate Limit / Quota Guard |
| :--- | :--- | :--- |
| **Google Places & Routes** | POI details, geocoding, multi-modal routes | Cached in Redis; batch text search |
| **Google Gemini Flash 2.5** | Intent parsing, POI relevance filtering | Prompt hashing cache; fallback to basic regex |
| **Amadeus Flight & Hotel API**| Live hotel pricing & flight offers | OAuth2 token caching (20 min expiry) |
| **SerpAPI** | Alternative hotel price intelligence | On-demand search for top 5 candidates |
| **Pinecone Vector Store** | 768-dim similarity search for vibe match | Top-k cosine distance filtering |

---

## 🔒 Security & Auth Architecture

- **Auth Strategy:** OAuth2 Bearer Tokens (JWT) with HS256 algorithm.
- **Password Hashing:** Passlib with bcrypt scheme.
- **Interceptors:** Frontend Axios interceptor (`frontend/src/services/api.ts`) automatically attaches `Authorization: Bearer <token>` to protected endpoints and handles HTTP 401/403/422 responses with Sonner toast UI alerts.
