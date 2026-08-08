# 💻 Intelligent Travel Agent — Frontend Documentation

React 18 web application built with **TypeScript**, **Vite**, **TailwindCSS**, **Radix UI**, **Lucide React**, **Motion (Framer Motion)**, and **Sonner**.

---

## 📋 Directory Architecture

```
frontend/
├── src/
│   ├── components/                  # Core React Components
│   │   ├── hero-section.tsx         # Parallax hero landing page with natural language prompt input
│   │   ├── navbar.tsx               # Top navigation header with Auth login/profile controls
│   │   ├── login-modal.tsx          # User login and registration modal dialog
│   │   ├── planning-flow.tsx        # Multi-step wizard state machine & API orchestrator
│   │   ├── planning-interface.tsx   # Step 1: Initial questionnaire & preference selection
│   │   ├── trip-plan.tsx            # Final itinerary view & dynamic hydration engine
│   │   ├── trips-carousel.tsx       # Horizontal showcase carousel for curated trips
│   │   ├── FeatureHighlightSection.tsx
│   │   ├── ExperienceScrollSection.tsx
│   │   ├── FeatureImageSection.tsx
│   │   ├── MediaShowcaseSection.tsx
│   │   ├── Footer.tsx
│   │   ├── planning-sections/       # Specialized section selection step components
│   │   │   ├── places-to-visit.tsx  # POI discovery & selection section
│   │   │   ├── accommodations.tsx   # Hotel selection section with price & commute tags
│   │   │   ├── dining.tsx           # Restaurant & culinary experience section
│   │   │   ├── transportation.tsx   # Flight & local transit selection section
│   │   │   ├── activities.tsx       # Adventure & cultural activity section
│   │   │   ├── shopping.tsx         # Shopping & market experience section
│   │   │   └── wellness.tsx         # Spa, nature & relaxation section
│   │   ├── ui/                      # Primitive UI Components (Radix UI + Tailwind)
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── input.tsx
│   │   │   ├── textarea.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── separator.tsx
│   │   │   ├── tooltip.tsx
│   │   │   ├── avatar.tsx
│   │   │   └── sonner.tsx           # Toast notification provider
│   │   └── figma/
│   │       └── ImageWithFallback.tsx# Image loader with graceful fallback
│   ├── contexts/
│   │   └── AuthContext.tsx          # Global JWT authentication context & session store
│   ├── services/
│   │   └── api.ts                   # Axios REST API service client with interceptors
│   ├── utils/
│   │   └── poi-mapper.ts            # Data mapping & normalization utilities
│   ├── App.tsx                      # Top-level view router & state holder
│   ├── main.tsx                     # React DOM entrypoint
│   └── index.css                    # Tailwind directives & glassmorphism CSS
├── public/                          # Static public assets
├── package.json                     # NPM dependencies and scripts
├── vite.config.ts                   # Vite bundler configuration
├── tailwind.config.js               # TailwindCSS configuration
├── tsconfig.json                    # TypeScript compiler options
└── .env.example                     # Environment template file
```

---

## 🛠️ Environment Configuration & Setup

### **1. Install Dependencies**
```bash
cd frontend
npm install
```

### **2. Environment Variables (`frontend/.env`)**
Create a `.env` file in the `frontend/` directory (copy from `.env.example`):

```ini
# Backend API Base URL
VITE_API_URL=http://127.0.0.1:8000/api

# Google Maps JavaScript API Key (for map rendering & photo URLs)
VITE_GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

### **3. Development Server**
Start the Vite development server with HMR:
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔄 Core Frontend Workflows

### **1. Authentication State (`AuthContext.tsx`)**
- Persists JWT tokens in `localStorage` (`auth_token`).
- Automatically attaches token to Axios headers via `api.setToken(token)`.
- Restores session on load via `getCurrentUser()`.

### **2. Step-by-Step Planning Wizard (`PlanningFlow.tsx`)**
State machine coordinating the 8-step wizard:
1. `questionnaire` (`PlanningInterface`): User enters destination, dates, travelers, budget, pace, interests. Triggers `api.startPlanning()`.
2. `places` (`PlacesToVisitSection`): Calls `api.discoverPlaces()`. User selects POIs.
3. `accommodations` (`AccommodationsSection`): Calls `api.searchAccommodations()`. User selects hotels.
4. `dining` (`DiningSection`): Calls `api.searchDining()`. User selects restaurants.
5. `transportation` (`TransportationSection`): Calls `api.searchTransport()`. User selects flights/transit.
6. `activities` (`ActivitiesSection`): Calls `api.searchActivities()`.
7. `shopping` (`ShoppingSection`): Calls `api.searchShopping()`.
8. `wellness` (`WellnessSection`): Calls `api.searchWellness()`. Triggers `api.generateItinerary(sessionId)`.

### **3. Dynamic Itinerary Hydration (`TripPlan.tsx`)**
The `hydrateItinerary` function transforms the raw API response into a rich visual display:
- Maps place IDs to Google Photos references.
- Calculates daily budget breakdowns (Accommodation + Food + Activities + Transport).
- Formats price levels into Rupee scale (`₹` to `₹₹₹₹₹`).
- Renders day-by-day activity timelines with category icons (`sightseeing`, `food`, `activity`, `culture`, `wellness`).

---

## 🎨 Design Tokens & UI Aesthetics

- **Color Palette:** Dark luxury theme using slate gradients (`from-slate-900 via-purple-900 to-slate-900`), vibrant purple/blue accents (`bg-gradient-to-r from-blue-500 to-purple-500`).
- **Glassmorphism:** CSS backdrop blur filters (`backdrop-blur-xl`, `bg-black/20`, `border-white/10`).
- **Animations:** Fluid transitions powered by `motion/react` (Framer Motion).

---

## 🚀 Building for Production

To create an optimized production bundle:
```bash
npm run build
```
Preview the production build locally:
```bash
npm run preview
```
