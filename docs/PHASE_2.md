# Phase 2 — Planner + fixtures

## Goal

Turn typed `Preferences + Constraints` into a structured `Itinerary` via a single Gemini call with `response_schema`, backed by curated Jaipur and Goa place fixtures so the planner runs deterministically offline in tests and during the live demo if the Maps API is unreachable.

## What gets built

- Pydantic models that act as the typed contract at every module boundary:
  - [backend/app/models/preferences.py](../backend/app/models/preferences.py) — `Preferences`, `Constraints`, `TripInput` plus interest/budget/pace/diet/group enums and date validation.
  - [backend/app/models/itinerary.py](../backend/app/models/itinerary.py) — `Itinerary`, `Day`, `ItinerarySlot`, `TravelLeg`, `SlotPeriod`. This is the schema Gemini returns.
  - [backend/app/models/disruption.py](../backend/app/models/disruption.py) — `Disruption` discriminated union and `ChangeLogEntry`.
  - [backend/app/models/trip.py](../backend/app/models/trip.py) — `Trip` aggregate (Firestore document shape) and `TripSummary` (list projection).
  - Re-exports — [backend/app/models/__init__.py](../backend/app/models/__init__.py).
- Gemini wrapper with structured-output enforcement, TTL cache keyed by SHA-256 of inputs, and a `FakeGeminiClient` test double — [backend/app/clients/gemini.py](../backend/app/clients/gemini.py).
- `PlacesClient` Protocol with two implementations — [backend/app/clients/places.py](../backend/app/clients/places.py):
  - `LivePlacesClient` (Maps Places API, swap-in stub).
  - `FixturePlacesClient` reading `fixtures/places_{slug}.json` with case-insensitive destination matching and a TTL cache.
- Curated fixture data — [backend/fixtures/places_jaipur.json](../backend/fixtures/places_jaipur.json) and [backend/fixtures/places_goa.json](../backend/fixtures/places_goa.json).
- Initial planner with a locked system prompt and stable cache key — [backend/app/services/planner.py](../backend/app/services/planner.py).
- Stubs in place for Phase 4 — [backend/app/services/classifier.py](../backend/app/services/classifier.py), [backend/app/services/replanner.py](../backend/app/services/replanner.py).
- Tests:
  - [backend/tests/test_models.py](../backend/tests/test_models.py) — Pydantic validators (date inversion, length caps, enum coercion).
  - [backend/tests/test_places.py](../backend/tests/test_places.py) — Fixture loading, slug matching, interest-based ranking.
  - [backend/tests/test_planner.py](../backend/tests/test_planner.py) — Prompt assembly, cache-key stability, no-candidates error path.

## Dependencies / prerequisites

- Phase 1 complete: backend skeleton, `Settings`, Makefile.
- `GEMINI_API_KEY` populated in `.env` for live runs (tests do **not** need it — `FakeGeminiClient` is used).
- `PLACES_BACKEND` defaults to `live` in production; tests force `fixture` via `conftest.py`.
- Cached `cachetools` and `google-generativeai` listed in [backend/pyproject.toml](../backend/pyproject.toml).

## How to test locally

Backend tests:

```bash
cd backend && make test
```

Expected: `test_models.py`, `test_places.py`, and `test_planner.py` all pass with Gemini and Places fully mocked. Specifically:

- `test_plan_returns_itinerary_for_valid_inputs` — produces a 2-day Jaipur `Itinerary` from a canned Gemini response.
- `test_plan_passes_user_preferences_into_prompt` — verifies "Jaipur", "history", "food", "Hawa Mahal" appear in the user prompt.
- `test_plan_uses_stable_cache_key_for_identical_inputs` — same inputs hash to the same key (cache hit).
- `test_plan_raises_when_no_candidates_found` — destination "Atlantis" raises `PlannerError`.

Backend dev server:

```bash
cd backend && make dev

# Health probe (Phase 1)
curl http://localhost:8080/health
# → {"status":"ok"}
```

Phase 2 has no new HTTP routes — the planner is invoked through `POST /trips` once Phase 3 wires it up. To exercise the planner directly against the live Gemini API, drop into a Python REPL inside the venv:

```bash
cd backend
.venv/bin/python -c "
import asyncio, json
from app.clients.gemini import LiveGeminiClient
from app.clients.places import FixturePlacesClient
from app.services.planner import Planner
from app.models import Preferences, Constraints, Interest, BudgetTier, Pace, GroupComposition, DietaryPreference
from datetime import date
from pathlib import Path
import os

prefs = Preferences(interests=[Interest.HISTORY, Interest.FOOD], budget=BudgetTier.MID_RANGE, pace=Pace.BALANCED, dietary=DietaryPreference.VEG, cuisines=['rajasthani'], group=GroupComposition.COUPLE)
cons = Constraints(destination='Jaipur', arrival_date=date(2026,6,1), departure_date=date(2026,6,4), travelers=2, must_see=['Hawa Mahal'])
gemini = LiveGeminiClient(api_key=os.environ['GEMINI_API_KEY'], model='gemini-2.0-flash-exp')
places = FixturePlacesClient(fixtures_dir='fixtures')
itinerary = asyncio.run(Planner(gemini=gemini, places=places).plan(prefs, cons))
print(json.dumps(itinerary.model_dump(mode='json'), indent=2))
"
```

Frontend: no UI changes in this phase — `npm run dev` continues to render the Phase 1 login page.

## Acceptance criteria

- `cd backend && make test` passes offline; no network calls to Gemini or Maps (rubric: Testing).
- All module boundaries are typed via Pydantic v2 — `Preferences`, `Constraints`, `Itinerary`, `Disruption`, `Trip` (rubric: Code Quality).
- Gemini calls are forced to `response_mime_type=application/json` with `response_schema=Itinerary` — no free-text parsing (rubric: Code Quality / Efficiency).
- Repeated identical planner calls hit the in-memory TTL cache (default 1h) — verified by `test_plan_uses_stable_cache_key_for_identical_inputs` (rubric: Efficiency).
- An explicit timeout (`external_call_timeout_seconds`, default 15s) is enforced on every Gemini call — see `LiveGeminiClient.generate_structured` (rubric: Efficiency).
- Planner raises `PlannerError` when no candidate places match the destination — never silently returns an empty itinerary.
- Fixture client falls back gracefully when no `places_{slug}.json` exists (returns `[]` and logs a warning) so the live Maps path can take over.
- Constraints validator rejects `departure_date <= arrival_date` and trip lengths > 14 days at the model layer (rubric: Security — input validation).

## Common failure modes

- **`GeminiError: Gemini response did not match schema`** — the model occasionally drops a required field. Confirm `gemini-2.0-flash-exp` (or whatever `GEMINI_MODEL` is set to) is reachable for your key; switch to `gemini-1.5-pro` if Flash is unstable.
- **Planner returns empty days for a real city** — `places_{slug}.json` does not exist for that destination. Either add a fixture or set `PLACES_BACKEND=live` and provision `GOOGLE_MAPS_API_KEY`.
- **`ValueError: GEMINI_API_KEY is required for LiveGeminiClient`** — startup happens lazily via `app.dependencies._build_gemini`; the error surfaces only on the first request hitting the planner. Set the key in `.env` and restart.
- **Tests fail with "No fixture file for destination 'jaipur '"** — slug normalization strips whitespace and lowercases; if you see this, check `_slugify` in `places.py` against your test input.
- **`asyncio` `TimeoutError` in production** — increase `external_call_timeout_seconds` for slow Gemini regions; default 15s is tight for `gemini-1.5-pro`.
- **Cache appears not to hit** — the cache is per-process in-memory (`TTLCache`). Multiple Cloud Run instances will each have their own copy. This is intentional for v1; document if measured cache-hit ratio is too low.
