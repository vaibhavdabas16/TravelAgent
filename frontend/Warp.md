# Warp Product Manual

## Project Overview

An AI-powered trip planner. The user describes a trip in one sentence, picks places, a hotel, transport and other options step by step, and gets a day-by-day itinerary with a map that can be saved to "My trips".

For setup, the folder structure and the design system, see [README.md](README.md). For the backend and the overall architecture, see [How It Works](../docs/HOW_IT_WORKS.md).

### Key Features

- **One-sentence brief**: `lib/trip-parser.ts` extracts destination, origin, dates, travelers, budget, pace, styles and must-haves; the user can edit every field before continuing.
- **Step-by-step planner**: Each step (places, accommodations, dining, transportation, activities, shopping, wellness) runs one backend search and lets the user pick results. From the stay step onward, "Build itinerary now" builds with what is selected so far; the steps from dining on can be skipped.
- **Streaming itinerary build**: The final build streams stage progress from the backend over Server-Sent Events.
- **Itinerary view**: Day selector, timeline and Leaflet map, with Overview, Stay and Flights tabs.
- **My trips**: Saved to the account when signed in, to `localStorage` when signed out; guest trips are uploaded on login.

## Technical Deep-Dive

### Core Components and Files

- **`src/main.tsx`**: React entry point.
- **`src/App.tsx`**: Routes with React Router: `/` (HomePage), `/plan` and `/plan/:sessionId/:stepId` (PlanPage), `/trip/:sessionId` (TripPage), `/trips` (TripsPage).
- **`src/services/api.ts`**: Axios client for auth, planning, saved trips and the SSE itinerary stream; attaches the JWT and shows toasts on 401/403/404/422.
- **`src/contexts/AuthContext.tsx`**: JWT session and guest-trip migration on login.
- **`src/lib/`**: Trip parser, step order (`planning-steps.ts`), session storage (`planning-storage.ts`), API-to-view-model mapping (`trip-model.ts`), saved trips, theme and formatting helpers.
- **`src/components/`**: `landing/`, `planning/`, `trip/` and `shared/` component groups.
- **`package.json`**: React 18, React Router 6, Vite 6, Tailwind CSS v4, Leaflet, Sonner and Lucide icons.

### Data Flow

1. **Brief**: On `/plan` the user types a sentence; the parsed brief is shown as editable fields.
2. **Session**: Continue calls `POST /api/v2/planning/start`, receives a `session_id` and moves to `/plan/:sessionId/places`.
3. **Steps**: Entering a step calls its search endpoint once and caches the results in `sessionStorage`, so going back or refreshing does not call the providers again. Leaving a step posts the selections.
4. **Build**: `POST /api/v2/planning/:sessionId/itinerary/stream` streams `collect → cluster → transport` progress, then returns the itinerary.
5. **Display**: `/trip/:sessionId` maps the response through `trip-model.ts`. Missing fields are hidden rather than filled with made-up data.
6. **Save**: "Save trip" calls `PUT /api/v2/saved-trips/:sessionId` when signed in, or stores the trip in `localStorage` otherwise.

The backend keeps planning sessions in memory, so if it restarts during a plan, the planner shows that the session is no longer available and the user starts again.
