# 💻 Intelligent Travel Agent — Frontend Documentation

React 18 web application built with **TypeScript**, **Vite**, **Tailwind CSS v4**, **Lucide React**, **Leaflet** (map) and **Sonner** (toasts). Utility-grade UI: one typeface, monochrome, lists over cards, no decorative imagery.

---

## 📋 Directory Architecture

```
frontend/
├── src/
│   ├── routes/
│   │   ├── HomePage.tsx             # Landing: headline, natural-language prompt, three facts
│   │   ├── PlanPage.tsx             # Planner: the brief, then one addressable step per search
│   │   ├── TripPage.tsx             # Itinerary: day timeline + map, Overview / Stay / Flights tabs
│   │   └── TripsPage.tsx            # My trips: account-backed when signed in, this browser otherwise
│   ├── components/
│   │   ├── shared/                  # Navbar, Footer, LoginModal, Photo, Toaster, empty/error states
│   │   ├── planning/                # TripPrompt, TripBrief, SelectionStep, PlaceRow, StepRail, PlanningProgress
│   │   └── trip/                    # DaySelector, ItineraryTimeline, MapPanel, HotelRow, FlightRow, LocalTransportPanel
│   ├── lib/
│   │   ├── trip-parser.ts           # Free text → destination, dates, travelers, budget, styles (client-side)
│   │   ├── trip-model.ts            # Normalises the API payload into the view model; never invents fields
│   │   ├── format.ts                # Money, durations, dates, photo/coord helpers (null when data is missing)
│   │   ├── planning-steps.ts        # Step order shared by router and planner
│   │   ├── planning-storage.ts      # sessionStorage working copy + localStorage fallback library
│   │   └── saved-trips.ts           # "My trips": account-backed for signed-in users, local fallback for guests
│   ├── services/api.ts              # Axios client: auth, planning endpoints, SSE itinerary stream
│   ├── contexts/AuthContext.tsx     # JWT session
│   └── index.css                    # Design tokens and the .btn / .field / .chip / .list / .row primitives
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
# Backend API Base URL — the client appends REST paths directly to this, so
# the /api suffix is required.
VITE_API_URL=http://127.0.0.1:8000/api
```

That's the only variable. The map is Leaflet over OpenStreetMap tiles, and place photos are served through the backend's photo proxy — neither needs a frontend API key.

### **3. Development Server**
Start the Vite development server with HMR:
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔄 Core Frontend Workflows

### **1. Authentication (`AuthContext.tsx`)**
- Persists JWT tokens in `localStorage` (`auth_token`), attaches them via an Axios interceptor, restores the session with `getCurrentUser()`.
- On login, `migrateLocalTripsToAccount()` uploads any trips saved as a guest to the account (best-effort, one bad trip doesn't block sign-in) and clears the local copies, so signing in never appears to lose a saved trip.

### **2. The brief (`/plan`)**
- The visitor types one sentence. `trip-parser.ts` extracts destination, origin, dates, travelers, budget tier (`budget | moderate | luxury`, the values the backend scores against), pace, travel styles and stay must-haves.
- Everything extracted is shown as editable fields ("Here's what we understood"). Nothing already answered is asked again.
- Continue calls `api.startPlanning()` and redirects to `/plan/:sessionId/places`.

### **3. Selection steps (`/plan/:sessionId/:stepId`)**
`places → accommodations → dining → transportation → activities → shopping → wellness`. Entering a step runs its search once and caches the result in sessionStorage, so back/refresh never re-bills the providers. Leaving a step posts its selections. From the stay step onward, "Skip ahead and build my itinerary" is available. The final build streams stage progress over SSE (`api.streamItinerary`).

### **4. Itinerary (`/trip/:sessionId`)**
`trip-model.ts` turns `{ itinerary: [{ day, title, stops, transport_legs }], recommended_hotels, recommended_flights, local_transport }` into a view model. Travel legs (mode, duration, distance) come straight from the backend; day insights ("stops are grouped within ~3 km") are derived from those legs only. Stops have no fabricated clock times, prices, weather or descriptions — a missing field hides its element. Selecting a timeline item highlights the map marker and vice versa.

"Save trip" writes through `lib/saved-trips.ts` (`PUT /api/v2/saved-trips/{sessionId}`) for a signed-in visitor, so **My trips** follows the account to any device and stays invisible to anyone else who signs into the same browser. A signed-out visitor falls back to a localStorage library, same as before; that fallback copy is uploaded to the account automatically on the next login.

---

## 🎨 Design System

Built with the [Hallmark](https://skills.sh/nutlope/hallmark) design skill — genre **atmospheric**, theme **Lumen** in both of its drops (**Night Foundry** dark by default, **Day Foundry** light via the sun/moon toggle in the nav — `lib/theme.ts`, persisted in `localStorage`, system preference as the fallback, applied before first paint by a script in `index.html`), macrostructure **Marquee Hero**. Tokens live in `frontend/tokens.css` (OKLCH, `--space-*`, `--text-*`, `--ease-*`, `--dur-*`), imported by `src/index.css` and mapped onto Tailwind v4 `@theme` names so components use `bg-paper`, `text-ink`, `border-rule`, `text-accent`.

- **Canvas** cool-violet near-black `oklch(13% .014 265)`; elevated surfaces step lighter. **Accent** molten brass `oklch(76% .17 50)` for the one primary button, selection, focus and the apparatus; **coral chord** `oklch(68% .16 18)` only for the single verb landmark in a headline.
- **Type** Instrument Serif (display, roman, lowercase for authored copy — data is never transformed) · Geist (body) · JetBrains Mono (UPPERCASE readouts: eyebrows, meta, `kbd`).
- **Landing** Marquee Hero on a blueprint grid: lowercase serif statement left, the **apparatus** right (`components/landing/Apparatus.tsx` — the seven real agent/provider files orbiting the planning session, light walking the edges), a **meter strip** of real counts, then the prompt, the pipeline as a four-column **ledger** (stage · does · calls · returns, every value read from `routes_planning.py`), three honest numbers, and an Ft5 statement footer.
- **Nav** N5 floating pill (fixed on the landing page, in-flow above a sticky context bar on product pages); the ⌘K / Ctrl K palette (`components/shared/CommandPalette.tsx`) remains the fast path.
- **Motion** three primitives — apparatus pulse + edge walk · reveal (section heads, verb underline) · card lift — all behind `prefers-reduced-motion`. The map's tiles are inverted into the palette with a CSS filter.

Project memory for the skill is in `.hallmark/` (`preflight.json`, `log.json`); the next `hallmark` run rotates away from this structure, nav and footer.

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
