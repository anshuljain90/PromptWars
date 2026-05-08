# Phase 1 — Scaffold + auth

## Goal

Stand up a deployable repo skeleton with FastAPI on the backend, Next.js on the frontend, and Firebase Authentication wired end-to-end so a Google sign-in produces a verified ID token that the backend accepts on `/me`.

## What gets built

- Repo root: [README.md](../README.md), [LICENSE](../LICENSE), [.env.example](../.env.example), [.gitignore](../.gitignore), [Makefile](../Makefile), [firebase.json](../firebase.json), [firestore.rules](../firestore.rules)
- Backend FastAPI app entrypoint with CORS, rate limit, and exception handlers — [backend/app/main.py](../backend/app/main.py)
- Pydantic-Settings driven environment loader — [backend/app/settings.py](../backend/app/settings.py)
- Firebase Admin ID-token verification dependency producing an `AuthenticatedUser` — [backend/app/auth.py](../backend/app/auth.py)
- Liveness probe — [backend/app/routes/health.py](../backend/app/routes/health.py)
- `/me` route that confirms the bearer token was accepted — declared in [backend/app/main.py](../backend/app/main.py)
- Backend Makefile targets (`install`, `dev`, `test`, `lint`, `format`, `docker`) — [backend/Makefile](../backend/Makefile)
- Cloud-Run-ready container — [backend/Dockerfile](../backend/Dockerfile)
- Pyproject with pinned deps (`fastapi`, `firebase-admin`, `slowapi`, `pytest`) — [backend/pyproject.toml](../backend/pyproject.toml)
- Next.js 15 App Router with `output: "export"` — [frontend/next.config.ts](../frontend/next.config.ts)
- Root layout with skip-link, `lang="en"`, `AuthProvider`, and `LiveAnnouncerProvider` — [frontend/app/layout.tsx](../frontend/app/layout.tsx)
- Firebase JS SDK init, Google sign-in helper, auth state listener — [frontend/lib/firebase.ts](../frontend/lib/firebase.ts)
- React `AuthProvider` exposing `useAuth()` — [frontend/components/auth/AuthProvider.tsx](../frontend/components/auth/AuthProvider.tsx)
- Login page with Continue-with-Google button — [frontend/app/page.tsx](../frontend/app/page.tsx)
- Typed API client that attaches the Firebase ID token as a Bearer header — [frontend/lib/api.ts](../frontend/lib/api.ts)
- Health endpoint test — [backend/tests/test_health.py](../backend/tests/test_health.py)

## Dependencies / prerequisites

- Python 3.12 (3.11+ accepted by `pyproject.toml`); a venv is created on first `make install`.
- Node 20+ and npm.
- A Firebase project with **Authentication → Google provider** enabled.
- A Google Cloud project linked to the Firebase project.
- A Firebase Admin service account JSON downloaded locally (only for dev — Cloud Run uses ADC).
- `.env` populated from [.env.example](../.env.example) — at minimum `FIREBASE_PROJECT_ID`, `GOOGLE_APPLICATION_CREDENTIALS`, `ALLOWED_ORIGINS`, and the four `NEXT_PUBLIC_FIREBASE_*` web-config values.

## How to test locally

Backend tests:

```bash
cd backend && make install
cd backend && make test
```

Expected: `tests/test_health.py` passes (returns `{"status": "ok"}`).

Backend dev server:

```bash
cd backend && make dev
# in another shell
curl http://localhost:8080/health
# → {"status":"ok"}

curl -i http://localhost:8080/me
# → HTTP/1.1 401 Unauthorized — "Missing bearer token"
```

Frontend dev server:

```bash
cd frontend && npm install
cd frontend && npm run dev
```

User-facing acceptance steps:

1. Open http://localhost:3000 — login page renders the "Continue with Google" button.
2. Click the button. Firebase popup completes sign-in.
3. The page redirects to `/trips` (the trips list — empty until Phase 3 ships CRUD UI).
4. In DevTools console: `await firebase.auth().currentUser.getIdToken()` yields a JWT. Calling `GET /me` against the backend with that JWT returns `{ uid, email, name }`.
5. Click **Sign out** in the header — back to `/`.

## Acceptance criteria

- `cd backend && make test` passes offline (rubric: Testing).
- `GET /health` returns 200 and `{"status":"ok"}` (Cloud Run liveness target).
- `GET /me` returns 401 without a token, 200 with a valid Firebase ID token, 401 with a malformed/expired token (rubric: Security).
- CORS is restricted to `ALLOWED_ORIGINS` from settings — never `*` (rubric: Security).
- A rate limit (`rate_limit_per_minute`, default 30/min) is wired via `slowapi` middleware (rubric: Security/Efficiency).
- Frontend loads with `lang="en"`, a visible skip-link on focus, a single `h1`, an `aria-live` region from `LiveAnnouncerProvider`, and no clickable `<div>`s (rubric: Accessibility).
- No secrets in source — every credential read from `Settings`/`process.env` (rubric: Security).
- Firebase Hosting + Firestore Rules configs present in repo root so deploy works without manual edits (rubric: Code Quality / Antigravity-deployable).

## Common failure modes

- **401 on `/me` with a valid token** — `FIREBASE_PROJECT_ID` mismatch, or `GOOGLE_APPLICATION_CREDENTIALS` points at a service-account JSON for a different project. Confirm the project ID matches the one issuing the token.
- **Sign-in popup blocked or returns `auth/unauthorized-domain`** — add `localhost` (and your eventual Hosting domain) under Firebase Console → Authentication → Settings → Authorized domains.
- **CORS error in browser when calling `/me`** — `ALLOWED_ORIGINS` does not include `http://localhost:3000`. Update `.env` and restart `make dev`.
- **`firebase-admin` raises `DefaultCredentialsError` on startup** — set `GOOGLE_APPLICATION_CREDENTIALS` to an absolute path of a valid service-account JSON, or run with ADC (`gcloud auth application-default login`).
- **Frontend throws "Firebase config missing"** — the four `NEXT_PUBLIC_FIREBASE_*` vars must be present at build/start time; restart `npm run dev` after editing `.env`.
- **`make install` fails on `python3.12`** — fall back to `python3 -m venv .venv` manually, or install Python 3.12 via pyenv/Homebrew.
