# Phase 4 — Disruption flow

## Goal

Make "real-time updates" demonstrable: a deterministic rule-based classifier picks the affected slots, a focused Gemini re-planner patches **only** those slots (preserving the rest of the trip), the new itinerary lands in Firestore, the frontend's `onSnapshot` listener fires, the affected card animates out, the replacement animates in, the change-log gains an entry, and a screen-reader announcement is fired — all without a page reload.

## What gets built

Backend:

- Rule-based disruption classifier — [backend/app/services/classifier.py](../backend/app/services/classifier.py):
  - `closure` → match every slot whose `place_id` equals the disrupted place.
  - `weather` → match slots on `day_index` whose `period` matches and whose `tags` include `outdoor`.
  - `traffic` → match the route edge between `from_slot_id` and `to_slot_id` (mark the destination slot as affected).
  - Returns `ClassificationResult(affected_slot_ids, reasoning)`.
- Re-planner with a focused Gemini prompt that returns only replacement slots — [backend/app/services/replanner.py](../backend/app/services/replanner.py). The prompt emphasises preserving the rest of the trip and matching each replaced slot's intent (cultural / outdoor / food).
- `POST /trips/{trip_id}/disruptions` route wired through `classifier → places.search (alternatives) → replanner.patch → repo.update` — promotes the placeholder in [backend/app/routes/trips.py](../backend/app/routes/trips.py) to a real handler.
- A `ChangeLogEntry` is appended to the trip on every successful re-plan, capturing the disruption type, summary, affected slot ids, and the replacement place ids — see [backend/app/models/disruption.py](../backend/app/models/disruption.py).
- New tests — `backend/tests/test_classifier.py`, `backend/tests/test_replanner.py`, and an integration test in `backend/tests/test_trips_api.py` covering `inject disruption → fetch updated trip → verify changeLog`.

Frontend:

- `DisruptionPanel` component (REQUIRED demo surface per CLAUDE.md §5.3.1) — `frontend/components/DisruptionPanel.tsx`:
  - Three preset buttons: "Amber Fort closes for maintenance" (closure), "Heavy rain 3pm–6pm Day 2" (weather), "Highway shutdown Calangute–Baga" (traffic).
  - A free-form mode that lets the presenter pick a slot and a disruption type.
  - Calls `api.injectDisruption(tripId, payload)`; while pending, disables itself and announces "Re-planning…".
- `ChangeLog` component listing every `change_log` entry with timestamps and a one-line summary — `frontend/components/ChangeLog.tsx`.
- `ItineraryDay` card with Framer Motion animations: shake + fade-out on the affected slot, slide-in + green pulse on the replacement — `frontend/components/ItineraryDay.tsx`.
- `useTrip(tripId)` hook backed by Firestore `onSnapshot` so the trip updates as soon as the backend write commits — `frontend/lib/useTrip.ts`.
- The single-trip view at [frontend/app/trip/page.tsx](../frontend/app/trip/page.tsx) is upgraded from the Phase 3 placeholder to render the day cards, the disruption panel, and the change log.
- `aria-live="polite"` announcement via the existing [frontend/components/LiveAnnouncer.tsx](../frontend/components/LiveAnnouncer.tsx) — every replacement fires "Plan updated: <slot> replaced by <new slot> due to <reason>".

## Dependencies / prerequisites

- Phases 1, 2, and 3 complete.
- Backend `DisruptionClassifier` and `Replanner` shipped as stubs in Phase 2 — this phase fills in their `classify` / `patch` methods.
- The `Disruption` discriminated-union model already exists ([backend/app/models/disruption.py](../backend/app/models/disruption.py)) — frontend types mirror it in [frontend/lib/types.ts](../frontend/lib/types.ts).
- Firestore is reachable from the frontend (the same Firebase config used by Auth) — `getFirestore()` exists in [frontend/lib/firebase.ts](../frontend/lib/firebase.ts).
- `firestore.rules` already restrict `users/{uid}/...` reads/writes to the owner — the `onSnapshot` listener will be authenticated through the Firebase JS SDK.

## How to test locally

Backend tests:

```bash
cd backend && make test
```

Expected new passes:

- `test_classifier.py` — closure matches by `place_id`, weather matches outdoor slots in the affected period only, traffic marks the destination slot as affected. Edge cases: closure on a `place_id` not in the itinerary returns an empty list.
- `test_replanner.py` — patches return the same number of slots as `affected_slot_ids`, each replacement has a different `place_id` than the slot it replaces, and `slot_id` values match so the trip can merge cleanly.
- `test_trips_api.py::test_inject_disruption_appends_change_log_and_swaps_slot` — full flow from `POST /trips/{id}/disruptions` to a follow-up `GET` showing the updated itinerary and a non-empty `change_log`.

Backend dev server:

```bash
cd backend && make dev

# Create a trip first (see Phase 3 curl example), then inject a closure
TOKEN="<paste Firebase ID token>"
TRIP_ID="<trip id from POST /trips>"

curl -X POST "http://localhost:8080/trips/$TRIP_ID/disruptions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"closure","place_id":"jpr-amber-fort","reason":"closed for maintenance"}'
# → 200 with the updated Trip; change_log has one entry, the d1-m slot has a different place

curl -X POST "http://localhost:8080/trips/$TRIP_ID/disruptions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"weather","day_index":2,"period":"afternoon","condition":"thunderstorm"}'
# → outdoor afternoon slot on day 2 is replaced with an indoor alternative
```

Frontend dev server:

```bash
cd frontend && npm run dev
```

User-facing acceptance steps:

1. Sign in, create a Jaipur trip (Phase 3 flow).
2. Land on `/trip?id=<trip_id>`. Day cards render with the morning / afternoon / evening slots.
3. Click **Inject: Amber Fort closes**. Within ~1 second:
   - The Amber Fort card shakes, fades, and is replaced by a different place card sliding in with a green pulse.
   - A toast / banner reads "Plan updated: Amber Fort replaced by Nahargarh Fort — closed for maintenance".
   - The screen-reader region announces the same line.
   - The change-log gains an entry: `{at, disruption_type: "closure", summary, affected_slot_ids, replaced_with}`.
4. Open a second tab on the same trip URL. Click **Inject: Heavy rain 3pm–6pm Day 2** in tab 1 — the affected slot updates in **both** tabs simultaneously (proves Firestore `onSnapshot` push).
5. Open DevTools → Application → IndexedDB / Firestore → confirm the trip document's `change_log` array has the entries you saw in the UI.
6. Keyboard test: tab to **Inject: …**, press Enter, observe the affected card focus and the announcement firing.

## Acceptance criteria

- Affected-slot detection is **pure-rules and deterministic** — no LLM call in the classifier (rubric: Efficiency, Code Quality).
- The re-planner patches only the affected slots; the rest of the itinerary is byte-equal before and after — verified in `test_replanner.py` (rubric: Problem Statement Alignment — `dynamically`).
- The `change_log` is append-only — every disruption produces exactly one entry, never silently mutates without one (CLAUDE.md §5.3 "must never silently mutate the plan").
- The disruption surface (CLAUDE.md §5.3.1) is reachable from the trip view, has presets for all three disruption types, and shows before/after via the animation (rubric: Problem Statement Alignment).
- Real-time push works through Firestore `onSnapshot` — no polling, no WebSockets (rubric: Problem Statement Alignment, Efficiency).
- The change announcement uses `aria-live="polite"`; the affected card animation does not steal focus (rubric: Accessibility).
- The disruption endpoint is rate-limited via `slowapi` middleware to protect cost and prevent abuse (rubric: Security).
- Authorization is re-checked on the disruption endpoint — a user can only inject disruptions on their own trips (rubric: Security).

## Common failure modes

- **`POST /trips/{id}/disruptions` returns 200 but the UI doesn't update** — the frontend isn't subscribed via `onSnapshot`; it's still calling `api.getTrip` once. Confirm the trip view uses `useTrip(tripId)` and not the Phase 3 fetch-once effect.
- **`onSnapshot` fires but the page does not re-render** — the listener returns a `Trip` from a fresh `model_validate`; ensure React state is updated by `setTrip(...)` inside the snapshot handler, not via a stale ref.
- **Replanner returns slots whose `slot_id` differs from the affected ones** — the merge in the route handler will end up with both old and new slots. The replanner's prompt MUST instruct Gemini to keep the same `slot_id` values; assert this in `test_replanner.py`.
- **Closure disruption marks zero slots as affected** — the `place_id` from the disruption payload doesn't appear in the itinerary (e.g., the demo data uses a different prefix). Use the `place_id` from `GET /trips/{id}` directly in the disruption payload.
- **Weather classifier picks an indoor slot** — the slot's `tags` array does not include `"outdoor"`. The planner system prompt requires `outdoor`/`indoor` tags on every slot; check the canned itinerary or re-plan.
- **Frontend Firestore listener throws `permission-denied`** — the user's Firebase Auth session expired or `firestore.rules` is mis-deployed. Re-deploy with `firebase deploy --only firestore:rules`.
- **The whole trip gets re-planned instead of only the affected slots** — the route handler is calling `planner.plan()` instead of `replanner.patch()`. Re-read [backend/app/routes/trips.py](../backend/app/routes/trips.py); the disruption path must use the replanner.
- **Demo recovery** — if Gemini is rate-limited mid-demo, the replanner falls back to picking a place from `places.search()` matching the same intent tags (this fallback path is documented under CLAUDE.md §8.9 stop-and-cut rules — keep it deterministic).
