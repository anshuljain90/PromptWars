# Phase 3 — Trips CRUD + frontend list/form

## Goal

Wire the planner into authenticated HTTP routes that create, list, fetch, and delete user-scoped trips in Firestore, and ship the frontend pages that drive those routes — a trip list, a preferences/constraints form, and a single-trip view.

## What gets built

Backend:

- Trip CRUD router with full auth + user-scoped Firestore access — [backend/app/routes/trips.py](../backend/app/routes/trips.py):
  - `POST /trips` (planner-backed creation) returns `Trip` with status 201.
  - `GET /trips` returns a paginated list of `TripSummary` for the current user.
  - `GET /trips/{trip_id}` returns the full `Trip` (404 on missing **or** another user's trip — never leak existence).
  - `DELETE /trips/{trip_id}` returns 204.
  - `POST /trips/{trip_id}/disruptions` registered as 501 placeholder for Phase 4.
- Dependency-injection wiring for planner, replanner, Gemini, places, and trip repo — [backend/app/dependencies.py](../backend/app/dependencies.py).
- Firestore-backed `TripRepository` plus an `InMemoryTripRepository` test double under `users/{uid}/trips/{tripId}` — [backend/app/clients/firestore.py](../backend/app/clients/firestore.py).
- Integration tests covering create, list, get-by-id, delete, cross-user denial, and 401 on missing token — [backend/tests/test_trips_api.py](../backend/tests/test_trips_api.py).
- Shared fixtures (mocked auth, in-memory repo, stub planner) — [backend/tests/conftest.py](../backend/tests/conftest.py).

Frontend:

- Trip list page with pagination-ready API call, loading + error + empty states — [frontend/app/trips/page.tsx](../frontend/app/trips/page.tsx).
- New-trip form with the full preferences + constraints surface (interests, budget, pace, diet, cuisines, group, must-see/avoid, mobility, dates, travelers) — [frontend/app/trips/new/page.tsx](../frontend/app/trips/new/page.tsx) and [frontend/components/PreferencesForm.tsx](../frontend/components/PreferencesForm.tsx).
- Single-trip view at `/trip?id=…` (query-param-driven so it works under Next.js `output: "export"`) — [frontend/app/trip/page.tsx](../frontend/app/trip/page.tsx).
- Trip card component used in the list — [frontend/components/TripCard.tsx](../frontend/components/TripCard.tsx).
- Header with sign-out — [frontend/components/AppHeader.tsx](../frontend/components/AppHeader.tsx).
- Typed API methods (`listTrips`, `createTrip`, `getTrip`, `deleteTrip`, `injectDisruption`) — [frontend/lib/api.ts](../frontend/lib/api.ts).
- Mirror types for the backend Pydantic models — [frontend/lib/types.ts](../frontend/lib/types.ts).

## Dependencies / prerequisites

- Phase 1 (auth) and Phase 2 (planner + fixtures) complete.
- `FIREBASE_PROJECT_ID` populated in `.env`; service-account JSON path or ADC available so Firestore writes succeed locally.
- Firestore database created in the Firebase project (Native mode), in the same region as Cloud Run (`asia-south1` or similar).
- [firestore.rules](../firestore.rules) deployed (`firebase deploy --only firestore:rules`) so cross-user access is denied at the data layer too — defense in depth alongside the backend check.
- `NEXT_PUBLIC_API_BASE_URL` pointing at `http://localhost:8080` (or the deployed Cloud Run URL).

## How to test locally

Backend tests:

```bash
cd backend && make test
```

Expected: every test in `test_trips_api.py` passes — including:

- `test_create_trip_returns_201_with_planner_itinerary`
- `test_create_trip_persists_to_repository`
- `test_create_trip_rejects_inverted_dates` (400)
- `test_list_trips_returns_user_trips_only` (no cross-user leakage)
- `test_get_trip_denies_other_users_trip` (404 — never 403, to avoid leaking existence)
- `test_delete_trip_removes_owned_trip` (204)
- `test_disruption_endpoint_returns_501_until_phase_4`
- `test_unauthed_request_to_trips_returns_401`

Backend dev server:

```bash
cd backend && make dev

# Without a token — 401
curl -i http://localhost:8080/trips

# With a token (paste a JWT minted by the running frontend Firebase Auth)
TOKEN="<paste Firebase ID token>"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8080/trips
# → []

curl -X POST http://localhost:8080/trips \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "interests": ["history","food"],
      "budget": "mid_range",
      "pace": "balanced",
      "dietary": "veg",
      "cuisines": ["rajasthani"],
      "group": "couple"
    },
    "constraints": {
      "destination": "Jaipur",
      "arrival_date": "2026-06-01",
      "departure_date": "2026-06-04",
      "travelers": 2,
      "mobility_notes": "",
      "must_see": ["Hawa Mahal"],
      "must_avoid": []
    }
  }'
# → 201 with full Trip JSON
```

Frontend dev server:

```bash
cd frontend && npm run dev
```

User-facing acceptance steps:

1. Sign in with Google at http://localhost:3000.
2. Land on `/trips` — empty state copy and a **Plan a new trip** button visible.
3. Click **Plan a new trip** → `/trips/new`. Fill destination ("Jaipur"), dates, pick interests, budget, pace, diet, cuisines, group, must-see ("Hawa Mahal").
4. Click **Generate itinerary**. Spinner shows; `aria-live` announces "Generating your itinerary". Backend `POST /trips` returns and the URL changes to `/trip?id=…`.
5. Trip view renders destination, date range, summary, and the count of slots across days (full itinerary cards land in Phase 4).
6. Hit back to `/trips` — the new trip is the first card in the list.
7. From a Firestore console (or a curl with a different user's token), confirm a `users/<uid>/trips/<tripId>` document exists with the full trip shape.
8. Sign out, sign in as a second Google account — that user's trip list is empty.

## Acceptance criteria

- Every protected route requires a Firebase ID token; missing/invalid tokens return 401 (rubric: Security).
- Authorization is **scoped by `request.state.user.uid`** in every query — verified by `test_get_trip_denies_other_users_trip` and `test_list_trips_returns_user_trips_only` (rubric: Security).
- Cross-user `GET /trips/{id}` returns 404, not 403 — does not leak existence (rubric: Security).
- `GET /trips` is paginated via `limit` (1–100, default 20) and an opaque `cursor` (rubric: Efficiency).
- Pydantic validation on every request body returns 400 with structured errors (rubric: Code Quality / Security).
- Frontend pages are gated by `useAuth()`; unauthenticated users redirect to `/` (rubric: Security).
- The trip view uses `?id=` query params, not dynamic segments — required for `output: "export"` static builds (rubric: Code Quality).
- All form inputs have associated `<label htmlFor>` or wrapping labels; radio groups use `<fieldset>` + `<legend>`; the form is reachable and submittable via keyboard alone (rubric: Accessibility).
- "Generating your itinerary" announcement is fired through the global `LiveAnnouncerProvider` so screen readers hear it (rubric: Accessibility).
- All `Preferences` and `Constraints` fields from CLAUDE.md §5.2 are present in the form — interests, budget, pace, diet/cuisines, group, dates, travelers, destination, mobility, must-see, must-avoid (rubric: Problem Statement Alignment).

## Common failure modes

- **`POST /trips` returns 502 Bad Gateway** — `PlannerError` bubbled up. Check backend logs: usually a missing/invalid `GEMINI_API_KEY` or a destination with no fixture and `PLACES_BACKEND=fixture`. Switch to `live` or add the fixture.
- **Firestore writes fail with `PermissionDenied`** — service account lacks `roles/datastore.user`. Grant it on the GCP IAM page or use ADC tied to a developer account with edit access.
- **`GET /trips` returns an empty list even after creating a trip** — Firestore `order_by("updated_at")` requires a single-field index; the first query auto-creates one, but the response will fail until it builds (~1 minute on a fresh project).
- **CORS error on `POST /trips` from the frontend** — `ALLOWED_ORIGINS` does not contain `http://localhost:3000`. Edit `.env` and restart the backend.
- **Trip view shows "Missing trip id"** — link was constructed without the `?id=` query param; check that `TripCard` href reads `/trip?id=${trip_id}`.
- **`test_get_trip_denies_other_users_trip` fails after refactoring** — the route MUST scope every read by `user.uid`. Never accept a `trip_id` and look it up across the entire `trips` collection group.
- **Form submit does nothing** — at least one interest must be selected; the submit button is `disabled` while `state.interests.size === 0`. The form also exposes a small "Select at least one interest" alert.
