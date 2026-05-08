# PromptWars — Travel Planning & Experience Engine

Plan trips dynamically with preferences, constraints, and real-time updates.

## What it does

PromptWars generates a personalized day-by-day travel itinerary from your preferences (interests, budget, pace, dietary needs, group composition) and constraints (dates, destination, must-see/avoid places, accessibility needs). When something disrupts the plan — a venue closure, a traffic jam, or bad weather — only the affected segments are re-planned, animated visibly in the UI, and recorded in a per-trip change log. Built for the PromptWars hackathon (organized by Hack2Skill, powered by Google).

## Live demo

> **TODO (Phase 5):** add Cloud Run backend URL + Firebase Hosting frontend URL.

## Screenshots

> **TODO (Phase 5):** main planning flow, disruption injection panel, before/after itinerary.

## Problem statement alignment

The Status column will be filled honestly at submission time. See [CLAUDE.md §7.2](./CLAUDE.md) for the full table; populated at the end of Phase 5.

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

> **TODO (Phase 5):** exact `gcloud run deploy` + `firebase deploy --only hosting` commands, including Antigravity import flow.

## Demo guide for judges

> **TODO (Phase 5):** step-by-step demo walkthrough including disruption injection.

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
