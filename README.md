# PromptWars — Travel Planning & Experience Engine

Plan trips dynamically with preferences, constraints, and real-time updates.

## What it does

PromptWars generates a personalized day-by-day travel itinerary from your preferences (interests, budget, pace, dietary needs, group composition) and constraints (dates, destination, must-see/avoid places, accessibility needs). When something disrupts the plan — a venue closure, a traffic jam, or bad weather — only the affected segments are re-planned, animated visibly in the UI, and recorded in a per-trip change log. Built for the PromptWars hackathon (organized by Hack2Skill, powered by Google).

## Live demo

- **Frontend:** _to be filled at deploy_ (Firebase Hosting)
- **Backend:** _to be filled at deploy_ (Cloud Run)
- **Demo account:** sign in with any Google account; your trips are scoped to your UID.

## Screenshots

> Placeholder — capture at deploy: (1) preferences/constraints form, (2) itinerary view with map, (3) disruption panel triggering a re-plan, (4) change log entry.

## Problem statement alignment

Each row maps a problem-statement keyword to the feature in the running app and its honest current status. _Implemented_ means the feature is live in the deployed demo. _Planned for next phase_ means it is documented and partially scaffolded but not shipped in v1.

| Keyword | Feature | Status |
|---------|---------|--------|
| preferences | Interests selection (culture / food / adventure / nature / nightlife / shopping / history) | Implemented |
| preferences | Budget tier (budget / mid-range / luxury) | Implemented |
| preferences | Pace (relaxed / balanced / packed) | Implemented |
| preferences | Dietary preferences (veg / non-veg / vegan / cuisines) | Implemented |
| preferences | Group composition (solo / couple / family / friends) | Implemented |
| constraints | Trip dates (arrival, departure) | Implemented |
| constraints | Number of travelers | Implemented |
| constraints | Destination | Implemented |
| constraints | Mobility / accessibility requirements | Implemented |
| constraints | Must-see places (user-specified) | Implemented |
| constraints | Must-avoid places / categories | Implemented |
| dynamic | AI-generated personalized day-by-day itinerary | Implemented |
| dynamic | Time-blocked structure (morning / afternoon / evening) | Implemented |
| dynamic | Per-place rationale tying back to user inputs | Implemented |
| dynamic + real-time | Re-plan of affected segments only (not whole trip) | Implemented |
| dynamic + real-time | Visible plan mutation without full page reload | Implemented |
| real-time + dynamic | Place closure / maintenance → alternative suggestion | Implemented |
| real-time + dynamic | Traffic disruption → reorder / reroute | Implemented |
| real-time + dynamic | Weather impact → indoor swap | Implemented |
| real-time | Visible change notification (toast / badge / highlight) | Implemented |
| real-time | Per-trip change-log of disruptions applied | Implemented |
| real-time + dynamic | Disruption injection demo surface (manual trigger for judges) | Implemented |
| real-time | (Stretch) Other disruptions — strikes, civic alerts | Planned for next phase |
| real-time | Background auto-detection (Cloud Scheduler + Pub/Sub poll for weather/closures) | Planned for next phase |

## Architecture

```
Next.js 15 (Firebase Hosting, static export) ──HTTPS──▶ FastAPI on Cloud Run
        │                                                       │
        ├─ Firebase Auth (Google sign-in)                        ├─ Vertex AI / Gemini (planner + replanner)
        ├─ Firestore onSnapshot (real-time push)                 ├─ Google Maps Places + Distance Matrix
        └─ Google Maps JS SDK (animated map)                     ├─ Cloud Firestore (per-user trips)
                                                                 └─ Secret Manager (API keys in prod)
```

A single FastAPI service holds all server logic in clean modules:

- `services/planner.py` — initial itinerary (one Gemini call, structured JSON)
- `services/replanner.py` — patches affected slots only (preserves the rest of the trip)
- `services/classifier.py` — pure-rules detection of which slots a disruption affects
- `clients/places.py` — Google Maps Places (live) with a fixture fallback for tests/demo
- `clients/routes.py` — Google Distance Matrix
- `clients/firestore.py` — typed trip repository

**Why a modular monolith, not microservices or a multi-agent framework:** see [CLAUDE.md §10 Decision Log](./CLAUDE.md). Optimized for delivery risk and demo reliability over architectural novelty.

## Google services used

| Service | Role |
|---|---|
| Gemini API (Vertex AI / AI Studio) | Initial itinerary generation + slot-level re-planning |
| Google Maps Places API | Discovery of candidate places by destination + interest |
| Google Maps Distance Matrix | Travel time + distance between itinerary stops |
| Firebase Authentication | Google sign-in; backend verifies ID token |
| Cloud Firestore | Per-user trip persistence + real-time `onSnapshot` push to UI |
| Cloud Run | Backend container hosting |
| Firebase Hosting | Frontend static asset hosting + CDN |
| Secret Manager | API keys in production (never committed) |

## Setup / run locally

### Prerequisites

- Python 3.11+
- Node 20+
- A Firebase project with Authentication (Google provider) enabled
- A Google Cloud project with the Gemini API and Maps Platform APIs enabled
- API keys: `GEMINI_API_KEY`, `GOOGLE_MAPS_API_KEY`, Firebase web config

### Steps

1. `cp .env.example .env` and fill in the values.
2. **Backend**:
   ```bash
   cd backend
   make install   # creates .venv, installs deps
   make test      # runs pytest
   make dev       # starts uvicorn on :8080
   ```
3. **Frontend** (in a second terminal):
   ```bash
   cd frontend
   npm install
   npm run dev    # starts Next.js on :3000
   ```
4. Open http://localhost:3000 and sign in with Google.

## Run tests

```bash
# Backend
cd backend && make test

# Frontend
cd frontend && npm test
```

All external dependencies (Gemini, Maps, Firestore, Firebase Auth) are mocked in tests — runs offline.

## Deployment

The repo deploys cleanly to Google Cloud — both via Antigravity import (the hackathon's expected path) and via `gcloud` directly.

### Prereqs (one-time per project)

```bash
# Replace with your project id; both Firebase + GCP point at it.
export GCP_PROJECT=<your-project-id>
export REGION=asia-south1

gcloud config set project $GCP_PROJECT
gcloud services enable \
  run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com \
  firestore.googleapis.com places-backend.googleapis.com \
  generativelanguage.googleapis.com

# Store secrets (never commit them):
echo -n "$GEMINI_API_KEY"      | gcloud secrets create gemini-api-key      --data-file=-
echo -n "$GOOGLE_MAPS_API_KEY" | gcloud secrets create google-maps-api-key --data-file=-
```

### Backend (Cloud Run)

```bash
cd backend
gcloud run deploy promptwars-api \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --set-secrets="GEMINI_API_KEY=gemini-api-key:latest,GOOGLE_MAPS_API_KEY=google-maps-api-key:latest" \
  --set-env-vars="FIREBASE_PROJECT_ID=$GCP_PROJECT,ALLOWED_ORIGINS=https://$GCP_PROJECT.web.app,PLACES_BACKEND=live"
```

This builds the `Dockerfile`, pushes to Artifact Registry, and deploys. Cloud Run surfaces the service URL — paste it into the frontend's `NEXT_PUBLIC_API_BASE_URL`.

### Frontend (Firebase Hosting)

```bash
cd frontend
NEXT_PUBLIC_API_BASE_URL=https://promptwars-api-...-asia-south1.run.app \
  npm run build         # writes static assets to out/

firebase deploy --only hosting,firestore:rules
```

### Antigravity import

Import this repo into Antigravity → it detects the `Dockerfile` for the backend and the `firebase.json` for the frontend, runs `cloudbuild.googleapis.com` for the API, and deploys both targets. Ensure the env vars / secrets above are configured in Antigravity's UI before the first run.

## Demo guide for judges

1. **Open the live URL** (top of this README).
2. **Sign in** — click _Continue with Google_, pick any Google account. Your trips are private.
3. **Plan a trip**:
   - Destination: `Jaipur` (or `Goa` — both are pre-fixtured)
   - Dates: any 2–3 day window in the future
   - Interests: pick at least one (e.g., `History` + `Food`)
   - Click _Generate itinerary_. Within a few seconds you'll be redirected to the trip view.
4. **See the dynamic plan** — three time-blocked cards per day with rationale, address, duration, and cost.
5. **Trigger a real-time disruption** (the most important demo step):
   - Right side of the trip view → _Real-time disruption demo_ panel.
   - Click _Close iconic outdoor stop_ — watch the affected card animate out and a new indoor card animate in. The card glows green for ~half a second to draw attention.
   - The change-log below records what happened with a timestamp.
   - Try _Heavy rain, Day 1 afternoon_ next — the same flow with a weather story.
   - The screen-reader-friendly `aria-live` region announces each update.
6. **Verify the plan persisted** — refresh the page; the trip + change log are intact (Cloud Firestore).
7. **Trip list** — click _All trips_ in the header; multiple trips list, ordered by latest update.

## Tech stack

- **Backend:** Python 3.12, FastAPI, Pydantic v2, google-generativeai, googlemaps, firebase-admin, google-cloud-firestore, slowapi (rate limiting), pytest
- **Frontend:** Next.js 15 (App Router, static export), TypeScript, Tailwind CSS, Radix UI, Framer Motion, Firebase JS SDK, Google Maps JS API, Vitest
- **Infrastructure:** Cloud Run (backend), Firebase Hosting (frontend), Cloud Firestore (data), Secret Manager (secrets)

## Known limitations

- Auto-detection of weather/traffic/closure disruptions via Cloud Scheduler is **planned for next phase**. v1 supports manual disruption injection (the required demo surface) only.
- Demo cities pre-fixtured: Jaipur and Goa. Other destinations work via live Maps API.
- Single-destination, multi-day trips only (per problem-statement scope). Multi-city itineraries out of scope.

## License

MIT — see [LICENSE](./LICENSE).
