# Phase 5 — Polish + deploy

## Goal

Land the demo seed data, fill the README so human judges can read and demo the app, hit Lighthouse Accessibility ≥ 90 on the trip view, and deploy the backend to Cloud Run + the frontend to Firebase Hosting so the live URL is available at submission time.

## What gets built

- Demo seed script that creates a `demo@example.com` Firebase user with two pre-saved trips (Jaipur + Goa) — `backend/scripts/seed_demo.py`. Idempotent — safe to re-run.
- Lighthouse audit pass on `/trip?id=<demo trip>` — accessibility ≥ 90; remediations land directly in the existing components ([frontend/components/PreferencesForm.tsx](../frontend/components/PreferencesForm.tsx), `frontend/components/ItineraryDay.tsx`, `frontend/components/DisruptionPanel.tsx`).
- README sections filled in:
  - **Live demo URL** — Cloud Run + Firebase Hosting links — [README.md](../README.md) §"Live demo".
  - **Screenshots / GIF** — main planning flow + disruption-injection panel + before/after — [README.md](../README.md) §"Screenshots".
  - **Problem statement alignment table** — every keyword (`dynamically`, `preferences`, `constraints`, `real-time updates`) mapped to a feature with `Implemented` / `Planned` honesty — [README.md](../README.md) §"Problem statement alignment".
  - **Demo guide for judges** — step-by-step "log in → load demo trip → inject disruption → see change log" — [README.md](../README.md) §"Demo guide for judges".
  - **Deployment** — exact `gcloud run deploy` and `firebase deploy --only hosting` commands plus the Antigravity import flow — [README.md](../README.md) §"Deployment".
- Backend deploy artefacts already present from Phase 1 — [backend/Dockerfile](../backend/Dockerfile), `cloudbuild.yaml` if added.
- Frontend static export wired and verified — [frontend/next.config.ts](../frontend/next.config.ts) sets `output: "export"`, `npm run build` produces `frontend/out/`, [firebase.json](../firebase.json) hosts that directory.
- Decision Log appended in CLAUDE.md §10 with all phase-2 through phase-5 architectural calls.

## Dependencies / prerequisites

- Phases 1–4 complete and merged into `main`.
- A Firebase project with Authentication (Google), Firestore (Native mode), and Hosting enabled.
- A GCP project linked to the Firebase project, with billing enabled.
- APIs enabled: Cloud Run Admin, Cloud Build, Artifact Registry, Secret Manager, Firestore, Firebase Hosting, Vertex AI / Generative Language, Maps Places, Distance Matrix.
- Service account `promptwars-backend@<project>.iam.gserviceaccount.com` with: `roles/datastore.user`, `roles/secretmanager.secretAccessor`, `roles/run.invoker` (when invoked by Hosting rewrites).
- Secrets in Secret Manager: `gemini-api-key`, `google-maps-api-key`, `firebase-project-id`. Loaded as env vars at deploy time via `--set-secrets`.
- `gcloud`, `firebase`, and `node` CLIs installed and authenticated locally; Antigravity IDE access for the submission import flow.

## How to test locally

Backend tests:

```bash
cd backend && make test
cd backend && make lint
```

All tests from Phases 1–4 still pass; lint is clean.

Run the demo seed locally against the Firebase emulator (or a dev Firebase project):

```bash
cd backend
.venv/bin/python scripts/seed_demo.py
# → seeded user demo@example.com (uid=...) with trips: jpr-demo-trip, goa-demo-trip
```

Backend dev server (final smoke):

```bash
cd backend && make dev

curl http://localhost:8080/health
# → {"status":"ok"}
```

Frontend dev server + production build:

```bash
cd frontend && npm run dev
# Manual flow: sign in, load a demo trip, inject every disruption preset, watch the change-log grow.

cd frontend && npm run build
# Static export in frontend/out/ — sanity check that the build succeeds before deploying.

npx serve frontend/out -p 3001
# Open http://localhost:3001 — the static bundle should behave identically to dev.
```

Lighthouse audit:

```bash
# With the trip view open in Chrome, run:
# DevTools → Lighthouse → Categories: Accessibility → Analyze page load
# Target: Accessibility >= 90.
```

User-facing acceptance steps (against the deployed URL):

1. Open the Firebase Hosting URL in incognito.
2. Sign in with the demo Google account (or the seeded `demo@example.com` if email/password seeding is configured).
3. Land on `/trips` — the Jaipur and Goa demo trips are visible without any creation step.
4. Open the Jaipur trip. Click **Inject: Amber Fort closes for maintenance** — the slot animates out, the replacement animates in, the change log gains an entry, the screen reader announces the change.
5. Repeat with the weather and traffic presets.
6. Sign out, sign back in as a different Google account — the demo trips are not visible (per-user isolation holds in production).
7. Open Lighthouse on the trip view in incognito on the deployed URL — Accessibility ≥ 90.

## Acceptance criteria

- The deployed Cloud Run URL responds 200 to `/health` over HTTPS (rubric: Security — HTTPS-only).
- The deployed Firebase Hosting URL serves the Next.js static export and connects to the deployed backend (CORS lists exactly the Hosting domain — never `*`) (rubric: Security).
- Secrets are sourced from Secret Manager in production — `.env` is **not** in the container; verified via `gcloud run services describe` showing `--set-secrets` mappings (rubric: Security).
- `seed_demo.py` is idempotent — running it twice does not duplicate trips. The script reads the demo Firebase UID from env (`DEMO_UID`) so it can be re-pointed without code edits.
- Lighthouse Accessibility ≥ 90 on the deployed trip view (rubric: Accessibility).
- README sections 1–13 from CLAUDE.md §7.2 are all present, screenshots embedded, demo URL working in incognito (rubric: Stage 2 / human judges).
- The Problem Statement Alignment table has Status filled in honestly — `Implemented` for the manual-injection flow, `Planned for next phase` for Cloud Scheduler auto-detection (rubric: Problem Statement Alignment).
- Five or more Google services are integrated and described in the README — Gemini, Maps Places, Distance Matrix, Firebase Auth, Firestore, Cloud Run, Firebase Hosting, Secret Manager (rubric: Google Services Usage).
- Decision Log in CLAUDE.md §10 has every meaningful architectural decision recorded with a one-line rationale (rubric: Code Quality / traceability).
- Antigravity-deployable: a fresh clone → Antigravity import → deploy succeeds without manual file edits — verified by re-importing into a clean workspace.

## Common failure modes

- **`gcloud run deploy` fails with `PERMISSION_DENIED` on Secret Manager** — the Cloud Run runtime service account lacks `roles/secretmanager.secretAccessor`. Grant it on each secret or at the project level.
- **`firebase deploy --only hosting` succeeds but the site shows a blank page** — the `frontend/out/` directory contains stale or partial build artefacts. Run `rm -rf frontend/out && cd frontend && npm run build` and redeploy.
- **CORS error from the deployed frontend to Cloud Run** — `ALLOWED_ORIGINS` env var on Cloud Run still says `http://localhost:3000`. Update via `gcloud run services update --update-env-vars ALLOWED_ORIGINS=https://<project>.web.app`.
- **`/me` works locally but returns 401 in production** — Cloud Run is using ADC (no `GOOGLE_APPLICATION_CREDENTIALS` set, which is correct), but the runtime service account lacks `roles/firebaseauth.viewer`. Grant the role and redeploy.
- **Lighthouse Accessibility < 90** — common offenders: insufficient color contrast on muted text, missing `aria-label` on icon-only buttons, focus-trap issues in dialogs. Audit the failing items by category and fix in the offending component file.
- **`seed_demo.py` errors with "USER_NOT_FOUND"** — Firebase Authentication does not allow programmatic email creation by default; the script uses `auth.create_user(...)` which requires `firebase-admin` initialized with project owner credentials. Run with the same service account used for deploys.
- **Demo trip `change_log` keeps growing** — the seed script is being re-run after disruptions have been injected; re-seeding overwrites the trips back to a clean state. This is intentional pre-demo; document it in the demo guide.
- **Antigravity import fails to build** — usually a `pyproject.toml` dep that's incompatible with Cloud Build's Python 3.12. Pin all backend deps; do not use `>=` in production.
- **Submission deadline pressure** — if Cloud Run deploy fails close to the deadline, the fallback is the Firebase Hosting URL pointing at a still-running localhost backend via a stable tunnel (e.g., `gcloud beta interactive` with port forwarding, or `cloudflared`). Document any such fallback honestly in README "Known limitations".
