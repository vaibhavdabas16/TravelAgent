# 🌍 Intelligent Travel Agent System

A production-grade, AI-powered multi-agent travel planning platform built with **LangGraph**, **FastAPI**, **React 18 (Vite + TypeScript)**, **Google OR-Tools**, **Amadeus API**, **Google Maps Platform**, **PostgreSQL**, and **Redis**.

---

## 📸 Overview & Value Proposition

The Intelligent Travel Agent System transforms free-form natural language prompts or structured preferences into fully optimized, multi-day travel itineraries. Unlike simple LLM wrappers, the system combines:

1. **Autonomous AI Agents (LangGraph)**: Specialized nodes for intent extraction, POI discovery, local expert scoring, accommodation selection, and flight/transit routing.
2. **Operations Research Optimization (Google OR-Tools)**: Solves the Vehicle Routing Problem with Time Windows (VRPTW) to construct realistic daily schedules that honor travel times, visit durations, and opening hours.
3. **Real-Time Data Providers**: Direct integration with Amadeus (flights & hotels), Google Maps (places, geocoding & routes), SerpAPI (price intelligence), and Pinecone (vector similarity search).
4. **Interactive Multi-Step UI**: A React 18 frontend wizard with dynamic step transitions, glassmorphism UI, real-time map hydration, and JWT user authentication.

---

## 🏗️ Repository Architecture

```
HCI_WORKING/
├── README.md                      <- Primary System Guide & Quickstart (This File)
├── ARCHITECTURE.md                <- Deep Technical Architecture & Multi-Agent Flow Specs
├── start_app.bat                  <- Windows Dual-Service Dev Server Launcher
│
├── backend/                       <- FastAPI & LangGraph Python Service
│   ├── app/
│   │   ├── agents/                <- LangGraph Nodes (Intake, Discovery, Optimizer, Accom, Transport)
│   │   ├── api/                   <- FastAPI REST Routes (V1, V2, Planning, Monitoring)
│   │   ├── db/                    <- SQLAlchemy Async Models & Database Sessions
│   │   ├── models/                <- Pydantic API Schemas & TravelAgentState TypedDict
│   │   ├── services/              <- Gemini, Google Maps, Amadeus, SerpAPI, Redis Cache, Cost Tracker
│   │   └── tools/                 <- Geocoding & Places search wrappers
│   ├── tests/                     <- Consolidated PyTest Integration & Unit Test Suite
│   ├── alembic/                   <- Database Schema Migrations
│   ├── README.md                  <- Detailed Backend Setup & API Docs
│   ├── main.py                    <- Uvicorn Application Entrypoint
│   └── requirements.txt           <- Python Dependencies
│
└── frontend/                      <- React 18 + Vite + TypeScript Web Application
    ├── src/
    │   ├── components/            <- Landing, Hero, Wizard Steps, Section Components & Trip Viewer
    │   ├── contexts/              <- AuthContext (JWT Session Management)
    │   ├── services/              <- api.ts (Axios REST API Client)
    │   ├── styles/                <- Tailwind & Custom Glassmorphism CSS
    │   ├── utils/                 <- POI Data Transformation Helpers
    │   ├── App.tsx                <- Application View Router
    │   └── main.tsx               <- React DOM Entrypoint
    ├── README.md                  <- Detailed Frontend Setup & Component Guide
    ├── package.json               <- Node Dependencies & Scripts
    └── vite.config.ts             <- Vite Configuration
```

For complete technical specifications, state graph definitions, and database schemas, refer to [ARCHITECTURE.md](ARCHITECTURE.md).

---

## ✨ System Capabilities

### 🤖 **1. Autonomous Multi-Agent Graph (LangGraph)**
- **Intake Node:** Extracts constraints (destination, dates, travelers, budget, vibe, must-see preferences) from natural language or structured forms.
- **Discovery Node:** Performs hybrid search across Google Places and Pinecone Vector DB (768-dim Gemini embeddings), filtered by an LLM validation step (`filter_irrelevant_pois`).
- **Optimizer Node:** Converts candidate POIs into a VRPTW model solved by Google OR-Tools, incorporating distance matrices, opening hours, and adaptive time window relaxation.
- **Accommodation Node:** Searches live hotel offers via Amadeus API, calculating a multi-factor score based on proximity to selected POIs, budget fit, and ratings.
- **Transport Node:** Fetches live flight offers (Amadeus) and multi-modal local transport routes (Google Routes API) between day stops.

### ⚡ **2. Enterprise Caching & Cost Tracking**
- **Layer 1 (API Cache):** Redis caching for place details (24h), geocoding (7 days), and routes (5 min).
- **Layer 2 (Session Cache):** Trip state persistence in Redis.
- **Layer 3 (LLM Cache):** Deterministic LLM response caching (30 days).
- **Cost Tracker:** Monitors Gemini and external API spend against quota limits.

### 🎨 **3. Interactive React 18 Web App**
- **Parallax Hero Landing Page:** Smooth carousel with location-segmented parallax animations.
- **8-Step Interactive Wizard:** Step-by-step preference selection for places, hotel preferences, dining, transportation, activities, shopping, and wellness.
- **Hydrated Itinerary Display:** Interactive map view with day-by-day activity timelines, weather indicators, daily budgets, hotel cards, and flight details.

---

## 🛠️ Quick Start Guide

### **Prerequisites**
- **Python:** 3.11 or higher
- **Node.js:** 18.0.0 or higher
- **PostgreSQL:** 14+ (or local SQLite fallback)
- **Redis:** 6+ (Optional, graceful degradation supported)

---

### **1. Environment Configuration**

Create `.env` files in both `backend/` and `frontend/` directories:

#### **Backend `.env` (`backend/.env`)**
```ini
# Core APIs
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GEMINI_API_KEY=your_gemini_api_key

# Travel Provider APIs
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
SERPAPI_KEY=your_serpapi_key

# Database & Cache
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/travel_db
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Security
JWT_SECRET=your_super_secret_jwt_key
```

#### **Frontend `.env` (`frontend/.env`)**
```ini
VITE_API_URL=http://127.0.0.1:8000/api
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

---

### **2. Running Local Dev Servers**

#### **Option A: Automatic Launcher (Windows)**
Run the included batch launcher to start both services concurrently:
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
- API Docs available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**Terminal 2 — Frontend (Vite + React):**
```bash
cd frontend
npm install
npm run dev
```
- Web Application available at: [http://localhost:5173](http://localhost:5173)

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
