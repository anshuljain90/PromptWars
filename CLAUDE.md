# CLAUDE.md — PromptWars: Travel Planning & Experience Engine

> This file is the source of truth for the project's mission, constraints, and acceptance criteria. It is loaded automatically by Claude Code at the start of every session. Read it fully before proposing any plan, writing any code, or making any architectural decision. Re-read it whenever scope feels unclear.

---

## 1. Mission

I am a **solo individual participant** in **PromptWars**, an AI-coding hackathon **organized by Hack2Skill and powered by Google**, with **200+ other individual participants** competing against me.

I have **~3 hours total** to design, build, test, deploy, and document a working application that solves the problem in Section 4 below. **Only my final submission counts** — there is no "best attempt" fallback. A half-finished feature in `main` at submission time is worse than no feature at all.

Your job (Claude Code) is to help me ship a polished, deploy-ready, demo-credible app that scores high on the evaluation rubric in Section 2 **and** survives a live human-judge demo.

---

## 2. Competition & Evaluation Framework

The submission is evaluated in **two stages**, by **two different audiences** with different concerns. Both must be excellent — optimizing only one is a losing strategy.

### Stage 1 — AI Code Assessment (creates the leaderboard)

An automated AI evaluator scans the **public GitHub repo** and scores it on the following seven signals. These are the **primary acceptance criteria** for every change in this project:

1. **Code Quality** — clean modular structure, strong typing on module boundaries, meaningful naming, no dead code, consistent error handling, linter/formatter passing.
2. **Security** — no hardcoded secrets, input validation on all external-facing endpoints, real authentication and authorization, safe and pinned dependencies, principle of least privilege.
3. **Efficiency** — async / non-blocking I/O for external calls, caching for expensive operations (LLM, Maps), no obvious N+1 patterns, sensible timeouts.
4. **Testing** — meaningful unit and integration tests with external dependencies mocked, runnable via a single command, passing cleanly at submission time.
5. **Accessibility** — semantic HTML, proper labels, keyboard navigability, WCAG AA contrast, ARIA where needed, screen-reader-friendly real-time announcements.
6. **Problem Statement Alignment** — the running app must visibly and demonstrably exhibit the keywords from the problem statement (see Section 4).
7. **Google Services Usage** — multiple Google-stack services integrated **meaningfully** (each doing real work, not name-dropped or decorative).

Top scorers on the leaderboard advance to Stage 2.

### Stage 2 — Human Judging (selects top 10)

Human judges **manually test the deployed app** and **read the README** to understand what was built. The README is the first thing they see — it must clearly explain the app, the architecture, and how to use the demo features.

### Top 10 → Live Presentation → Winner Announcement

**Implication for our work:** Stage 1 rewards code quality, structure, tests, and rubric coverage. Stage 2 rewards a working app, a clear README, and a smooth demo. **The README and the deployed app are not afterthoughts — they are half the score.**

---

## 3. Hard Constraints (non-negotiable)

- **MUST** deploy on **Google Cloud Platform**.
- **MUST** use the **Google stack meaningfully** — multiple services, real integration. No decorative usage.
- **MUST** be **deployable from Antigravity IDE** (Google's agentic IDE). The repo must contain everything Antigravity needs — build config, runtime config, documented env vars — so that a fresh import deploys cleanly without manual fixes.
- **MUST** be in a **public GitHub repo**.
- **MUST** ship a **comprehensive README** that human judges can use to understand and operate the app.
- **MUST** treat the seven evaluation signals (Section 2) as primary acceptance criteria for every change.
- **Time budget:** approximately **3 hours total**, single developer, working alone.
- **Developer profile:** software architect, **strong on backend**, **weak on frontend**. Bias decisions toward keeping the frontend minimal but correct (especially on accessibility), and putting most engineering effort behind a clean backend.

---

## 4. Problem Statement (verbatim from organizers)

> **Travel Planning & Experience Engine — Plan trips dynamically with preferences, constraints, and real-time updates.**

Three keywords carry the entire scoring weight on Problem Statement Alignment: **dynamically**, **preferences + constraints**, and **real-time updates**. The running app must visibly and demonstrably exhibit all three, and the README must explicitly map each keyword to the feature that satisfies it.

---

## 5. Functional Requirements

### 5.1 User Authentication (required)

- Login is required to access trip planning.
- Each user has their own private trips — no cross-user data leakage.
- Sessions persist across browser refreshes.
- Logout is supported.
- Auth must be implemented using a Google-stack identity service.

### 5.2 Trip Planning

**Scope (locked):** multi-day, single-destination trips (e.g., "3 days in Goa", "5 days in Jaipur"). **Not** multi-city itineraries. **Not** single-day trips. **Not** international (unless time permits as bonus, and only after all core flows are complete).

**Preferences the app must accept:**
- Interests (e.g., culture, food, adventure, nature, nightlife, shopping, history)
- Budget tier (budget / mid-range / luxury)
- Pace (relaxed / balanced / packed)
- Dietary preferences (veg / non-veg / vegan / specific cuisines)
- Group composition (solo / couple / family / friends)

**Constraints the app must accept:**
- Trip dates (arrival and departure)
- Number of travelers
- Destination
- Mobility / accessibility requirements
- Must-see places (user-specified)
- Must-avoid places or categories (user-specified)

**Output: a structured day-by-day itinerary** containing, for each day:
- Time-blocked activities (morning / afternoon / evening)
- Place name, type, location, brief description
- Estimated time at each activity
- Travel time and mode between activities
- Rough estimated cost per activity
- A one-line rationale for why each place was chosen, tied back to the user's preferences/constraints

### 5.3 Real-Time Dynamic Updates (CORE — heavily weighted on Problem Statement Alignment)

Once a trip is generated and saved, the itinerary must be **dynamic and adaptive**. The following events must trigger an automatic re-plan of **affected segments only** (do not re-plan the whole trip when one item changes):

1. **Place closure / maintenance** — a venue in the itinerary becomes unavailable → the app suggests an alternative matching the same intent and time slot.
2. **Traffic disruption** — a planned route between two stops becomes infeasible → the app reorders or reroutes affected segments.
3. **Weather impact** — an outdoor activity is scheduled during heavy rain or extreme heat → the app swaps to an indoor alternative for that slot.
4. **(Stretch) Other disruptions** — strikes, events, civic alerts. Optional, only if core three are solid.

The user must be **visibly notified** when an update has occurred — via a toast, badge, highlighted segment, or change-log entry. Updates must never silently mutate the plan.

#### 5.3.1 Demo / Test Surface (REQUIRED)

There **must** be a dedicated UI affordance — a screen, panel, or set of buttons — that lets the demo presenter **manually inject** any of the disruption types above against an existing plan, to **visibly trigger the re-plan in front of the judges**.

Without this, the entire "real-time" feature is invisible during evaluation. This is not optional, and it is not a "nice to have" — it is the single most important demo-time feature.

The injection surface should:
- Be reachable from the main trip view
- Allow selecting a specific itinerary item or segment to disrupt
- Allow choosing the disruption type (closure / traffic / weather)
- Show the before-and-after state clearly
- Persist a change-log entry for the trip

### 5.4 Trip Persistence

- Authenticated users can **save**, **list**, **open**, and **delete** their trips.
- Trips persist across sessions in a Google-stack datastore.
- A trip record includes:
  - Original preferences and constraints
  - Current itinerary
  - A change-log of real-time updates applied (what changed, when, why)

---

## 6. Non-Functional Requirements (mapped to evaluation rubric)

### 6.1 Code Quality (Rubric: Code Quality)

- Strong typing (static or runtime-validated) on all module boundaries — request/response shapes, data models, service contracts.
- Modular structure: routes / services / models / external clients are separated; no mega-files.
- No commented-out code, no dead files, no `print` / `console.log` debugging left in.
- Meaningful names — no `data`, `temp`, `x`, `helper`, `util` as primary names.
- Public functions have brief docstrings or JSDoc explaining intent.
- Linter and formatter configured, runnable via a single command, passing at submission.
- Consistent error-handling pattern across the codebase.

### 6.2 Security (Rubric: Security)

- **Zero secrets in source control** — every API key, credential, and connection string sourced from environment variables in dev and **Google Secret Manager** (or equivalent) in production.
- **Input validation** on every external-facing endpoint, with clear, safe error responses.
- **Authentication enforced** on every protected route — never trust the frontend.
- **Authorization** — a user can only read/modify their own trips. Tested.
- **CORS** configured to specific origins; never `*` in production config.
- **Rate limiting** on AI-calling and Maps-calling endpoints (cost protection + abuse protection).
- **HTTPS-only** (Cloud Run default — do not break it).
- Dependencies pinned, free of known critical CVEs at submission time.

### 6.3 Efficiency (Rubric: Efficiency)

- Async / non-blocking I/O for all external API calls.
- Cache LLM responses keyed by a normalized input hash, with a reasonable TTL.
- Cache Maps/Places lookups for repeated queries.
- Avoid redundant API calls — batch or memoize within a single request.
- Pagination on list endpoints (e.g., "my trips").
- Reasonable, explicit timeouts on every external call — never hang indefinitely.

### 6.4 Testing (Rubric: Testing)

- Unit tests on core business logic — trip generation, re-plan logic, validation, authorization checks.
- Integration tests on API endpoints — auth flow, create trip, inject disruption, fetch updated trip.
- All external dependencies (LLM, Maps, datastore, auth provider) **mocked** in tests. Tests must run offline, deterministically, in CI.
- Tests run via a single command; the README documents this command prominently.
- Coverage report is generatable and acceptable on core logic.
- Aim for tests that prove behavior, not just exercise code paths.

### 6.5 Accessibility (Rubric: Accessibility)

- **Semantic HTML** — `<main>`, `<nav>`, `<header>`, `<button>`, `<form>`, `<label for="...">`, etc. No clickable `<div>`s.
- All form inputs have associated labels (`<label>` or `aria-label`).
- **Color contrast** meets WCAG AA minimum.
- All interactive elements **reachable and operable via keyboard alone**.
- **Visible focus indicators** — never `outline: none` without a visible replacement.
- **ARIA `aria-live` regions** for real-time update notifications, so screen readers announce when the plan changes.
- Headings in correct hierarchical order (no skipping h1 → h3).
- Page passes a Lighthouse Accessibility audit with score **≥ 90**.

### 6.6 Problem Statement Alignment (Rubric: Problem Statement Alignment)

- Every keyword from the problem statement is observable in the running app:
  - **"dynamically"** → re-plans happen visibly without a full page reload, and the user sees what changed.
  - **"preferences"** → labeled, structured input — not free-text only.
  - **"constraints"** → labeled, structured input — not free-text only.
  - **"real-time updates"** → demonstrable via the test/injection surface in Section 5.3.1.
- The README explicitly maps each keyword to where in the app it lives, with screenshots.

### 6.7 Google Services Usage (Rubric: Google Services Usage)

The app must integrate the Google stack **meaningfully** — each service must do real work in the critical path, not be name-dropped.

**Available palette** (Claude Code proposes which to use during planning, with rationale per service. Do not commit to picks before the planning step):

- **Vertex AI / Gemini API** — generative reasoning for itinerary synthesis, preference parsing, and re-plan logic.
- **Google Maps Platform** — Places API (place discovery + details + status), Routes API (travel time + mode), Geocoding, Distance Matrix.
- **Firebase Authentication** — login (satisfies Section 5.1).
- **Cloud Firestore** — per-user trip persistence (satisfies Section 5.4).
- **Cloud Run** — deployment target (mandatory).
- **Cloud Build** — CI build (Antigravity will trigger this on import).
- **Secret Manager** — API key storage in production (satisfies Section 6.2).
- **Cloud Storage** — asset storage if needed (optional).
- **Cloud Scheduler / Pub/Sub** — periodic real-time disruption checks (optional, stretch).
- **Weather data** — Google does not have a universally-available first-party weather API; Claude Code may use Maps weather features if applicable, otherwise a free third-party source (e.g., open-meteo) — and the README must honestly document the choice.

**Target:** five or more Google services genuinely integrated, each with a clear role described in the README.

---

## 7. Submission Requirements

### 7.1 Public GitHub Repo

- Clean commit history with meaningful messages — not "wip", "test", "asdf".
- `.gitignore` covers env files, build artifacts, IDE cruft, OS junk.
- `.env.example` showing every required env var, with comments — no real values.
- A LICENSE file (MIT or Apache-2.0).
- No committed secrets — verified before push.

### 7.2 README.md (READ BY HUMAN JUDGES — write it for them)

Required sections, in this order:

1. **Project name + one-line tagline**
2. **What it does** — 2–3 plain-English sentences a non-technical judge can understand
3. **Live demo URL** — the deployed Cloud Run link
4. **Screenshots / GIF** — main flow + the real-time disruption demo
5. **Problem statement alignment** — explicit mapping of each problem-statement keyword (`dynamically`, `preferences`, `constraints`, `real-time updates`) to the feature that satisfies it
6. **Architecture overview** — a simple diagram or paragraph; what runs where, which Google services do what
7. **Google services used** — bulleted, with the role each service plays
8. **Setup / run locally** — exact commands, copy-pasteable
9. **Run tests** — exact command, copy-pasteable
10. **Deployment** — how this repo deploys to Cloud Run (and via Antigravity)
11. **Demo guide for judges** — step-by-step: log in, enter prefs/constraints, generate trip, **inject a disruption to see real-time update**, view updated plan and change log
12. **Tech stack** — short, declarative
13. **Known limitations / not implemented** — honesty wins trust; never claim what isn't real

### 7.3 Antigravity-Deployable

- The repo must contain everything Antigravity needs to build and deploy: build config (e.g., `Dockerfile` or service config), documented env vars, and any required config files.
- A fresh clone → Antigravity import → deploy must succeed without manual file edits.

### 7.4 Submission Form

A submission form will need to be filled out at submission time. Field details are not known at briefing time — fill carefully and double-check the deployed URL and the repo URL when submitting.

---

## 8. Working Agreement (rules of engagement for Claude Code)

These rules govern how we collaborate during the 3-hour sprint:

1. **Plan before coding.** When given a new objective, propose an approach with reasoning before creating files. For non-trivial decisions (stack picks, schema design, choice of Google service for a given role, third major dependency), **stop and confirm with me** before proceeding.
2. **Score every change against the rubric.** Before committing, mentally walk through the seven evaluation signals and confirm no regression. Mention any tradeoff explicitly.
3. **Tests are not optional.** Every business-logic module ships with tests in the same change. Do not defer "I'll add tests later" — there is no later.
4. **No secrets in code. Ever.** If a key is needed, add it to `.env.example` with a comment, document it in the README, and read it from the environment.
5. **Accessibility is built in, not retrofitted.** Use semantic HTML and proper labels from the very first component.
6. **Commit hygiene.** Atomic commits with descriptive messages. Do not squash everything into a single "final" commit at the end.
7. **Honest README.** If something doesn't fully work, document it under "Known limitations." Never claim a feature that isn't real.
8. **Stop and ask** when:
   - A decision changes the architecture or schema
   - About to add a fourth major dependency
   - About to skip a rubric requirement to save time
   - The scope is drifting beyond Section 5
   - Time on a task has exceeded its allocation by more than 50%
9. **Time-box ruthlessly.** We have ~3 hours. If a feature is over-running, **cut it cleanly** and document it as "not implemented" — do not ship broken or half-wired things.
10. **The final submission is the only one that counts.** No half-finished feature in `main` at submission. If it isn't done, it is removed before submitting.
11. **Keep me in the loop on every milestone.** After scaffolding, after auth working, after first trip generated, after disruption demo working, after deploy — surface progress so I can sanity-check direction.

---

## 9. Out of Scope (do not build)

- Multi-city or cross-country itineraries
- Flight or hotel booking integration (informational display is fine; no actual transactions)
- Payment processing of any kind
- Social or sharing features beyond a simple "share trip link" (and even that only if trivial)
- Mobile native apps (web only)
- Offline mode
- Multilingual UI (English only for v1)
- AI assistant chatbot UX — we are a structured planner, not a chat
- Group collaboration / real-time co-editing of a single trip by multiple users
- Email / SMS notifications
- Admin dashboards
- Analytics beyond what's free with Cloud Run

If a feature feels like it might be in scope but is not listed in Section 5, **stop and ask** before building it.

---

## 10. Decision Log

(Empty at start of project. Claude Code: append every meaningful architecture, stack, library, schema, or scope decision here as it is made, with a one-line rationale. This is how we maintain traceability for human judges and for ourselves.)

| # | Date/Time | Decision | Rationale |
|---|-----------|----------|-----------|
|   |           |          |           |

---

## 11. Glossary

- **Antigravity** — Google's agentic IDE; the deployment must originate from this tool.
- **Eval rubric** — the seven scoring signals in Section 2.
- **Re-plan** — the operation of regenerating only the affected segments of an itinerary in response to a real-time disruption.
- **Disruption** — any of: place closure, traffic disruption, weather impact (and stretch: other civic alerts).
- **Demo surface** — the UI affordance described in Section 5.3.1 that allows manual injection of disruptions during a live demo.
- **Stage 1** — AI code assessment producing the leaderboard.
- **Stage 2** — Human judges manually testing the deployed app to select the top 10.
