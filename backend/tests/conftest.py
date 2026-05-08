"""Shared pytest fixtures: mocked external clients and an authed test client."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import UTC, date, datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthenticatedUser, require_user
from app.clients.firestore import InMemoryTripRepository, TripRepository
from app.dependencies import get_planner, get_replanner, get_trip_repo
from app.main import app
from app.models import (
    BudgetTier,
    Constraints,
    Day,
    DietaryPreference,
    Disruption,
    GroupComposition,
    Interest,
    Itinerary,
    ItinerarySlot,
    Pace,
    Preferences,
    SlotPeriod,
    Trip,
    TripInput,
)
from app.services.planner import Planner
from app.services.replanner import Replanner


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tests must not pick up real keys from a developer's .env."""
    for var in (
        "GEMINI_API_KEY",
        "GOOGLE_MAPS_API_KEY",
        "FIREBASE_PROJECT_ID",
        "GOOGLE_APPLICATION_CREDENTIALS",
    ):
        monkeypatch.setenv(var, "test")
    monkeypatch.setenv("PLACES_BACKEND", "fixture")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:3000")
    os.environ["TESTING"] = "1"


@pytest.fixture
def fake_user() -> AuthenticatedUser:
    return AuthenticatedUser(uid="user-1", email="user@example.com", name="Test User")


@pytest.fixture
def trip_repository() -> InMemoryTripRepository:
    return InMemoryTripRepository()


class _StubPlanner:
    """Returns a fixed Itinerary regardless of inputs — for CRUD-flow tests."""

    def __init__(self, canned: Itinerary) -> None:
        self._canned = canned
        self.calls: int = 0

    async def plan(
        self,
        preferences: Preferences,
        constraints: Constraints,
    ) -> Itinerary:
        self.calls += 1
        return self._canned


@pytest.fixture
def stub_planner(sample_itinerary: Itinerary) -> _StubPlanner:
    return _StubPlanner(canned=sample_itinerary)


class _StubReplanner:
    """Replaces affected slots with canned ItinerarySlots — for endpoint tests."""

    def __init__(self, replacements: dict[str, ItinerarySlot] | None = None) -> None:
        self._replacements = replacements or {}
        self.calls: list[tuple[list[str], Disruption]] = []

    async def patch(
        self,
        itinerary: Itinerary,
        affected_slot_ids: list[str],
        disruption: Disruption,
    ) -> list[ItinerarySlot]:
        self.calls.append((list(affected_slot_ids), disruption))
        # Default: clone the affected slot but rename + tag indoor.
        out: list[ItinerarySlot] = []
        for sid in affected_slot_ids:
            if sid in self._replacements:
                out.append(self._replacements[sid])
                continue
            original = next(
                (s for d in itinerary.days for s in d.slots if s.slot_id == sid),
                None,
            )
            if original is None:
                continue
            out.append(
                original.model_copy(
                    update={
                        "place_id": f"{original.place_id}-alt",
                        "place_name": f"{original.place_name} (alt)",
                        "tags": ["indoor", *(t for t in original.tags if t != "outdoor")],
                        "rationale": "Indoor swap due to disruption.",
                    }
                )
            )
        return out


@pytest.fixture
def stub_replanner() -> _StubReplanner:
    return _StubReplanner()


@pytest.fixture
def authed_client(
    fake_user: AuthenticatedUser,
    trip_repository: InMemoryTripRepository,
    stub_planner: _StubPlanner,
    stub_replanner: _StubReplanner,
) -> Iterator[TestClient]:
    """A FastAPI TestClient with all critical deps mocked: auth, repo, planner, replanner."""

    async def _override_user() -> AuthenticatedUser:
        return fake_user

    def _override_repo() -> TripRepository:
        return trip_repository

    def _override_planner() -> Planner:
        return stub_planner  # type: ignore[return-value]

    def _override_replanner() -> Replanner:
        return stub_replanner  # type: ignore[return-value]

    app.dependency_overrides[require_user] = _override_user
    app.dependency_overrides[get_trip_repo] = _override_repo
    app.dependency_overrides[get_planner] = _override_planner
    app.dependency_overrides[get_replanner] = _override_replanner
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client() -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client


@pytest.fixture
def sample_preferences() -> Preferences:
    return Preferences(
        interests=[Interest.HISTORY, Interest.FOOD],
        budget=BudgetTier.MID_RANGE,
        pace=Pace.BALANCED,
        dietary=DietaryPreference.VEG,
        cuisines=["rajasthani"],
        group=GroupComposition.COUPLE,
    )


@pytest.fixture
def sample_constraints() -> Constraints:
    return Constraints(
        destination="Jaipur",
        arrival_date=date(2026, 6, 1),
        departure_date=date(2026, 6, 4),
        travelers=2,
        mobility_notes="",
        must_see=["Hawa Mahal"],
        must_avoid=[],
    )


@pytest.fixture
def sample_trip_input(
    sample_preferences: Preferences, sample_constraints: Constraints
) -> TripInput:
    return TripInput(preferences=sample_preferences, constraints=sample_constraints)


def _slot(slot_id: str, period: SlotPeriod, place: str, tags: list[str]) -> ItinerarySlot:
    return ItinerarySlot(
        slot_id=slot_id,
        period=period,
        place_id=f"pid-{slot_id}",
        place_name=place,
        place_type="attraction",
        address=f"{place}, Jaipur",
        lat=26.92,
        lng=75.82,
        description=f"{place} description",
        duration_min=120,
        estimated_cost_inr=500,
        rationale=f"Selected for {place}",
        tags=tags,
    )


@pytest.fixture
def sample_itinerary() -> Itinerary:
    """Two-day Jaipur itinerary used across replanner/classifier tests."""
    return Itinerary(
        days=[
            Day(
                day_index=1,
                date_iso="2026-06-01",
                slots=[
                    _slot("d1-m", SlotPeriod.MORNING, "Amber Fort", ["outdoor", "history"]),
                    _slot("d1-a", SlotPeriod.AFTERNOON, "City Palace", ["indoor", "history"]),
                    _slot("d1-e", SlotPeriod.EVENING, "Chokhi Dhani", ["indoor", "food"]),
                ],
            ),
            Day(
                day_index=2,
                date_iso="2026-06-02",
                slots=[
                    _slot("d2-m", SlotPeriod.MORNING, "Hawa Mahal", ["outdoor", "history"]),
                    _slot("d2-a", SlotPeriod.AFTERNOON, "Jantar Mantar", ["outdoor", "history"]),
                    _slot("d2-e", SlotPeriod.EVENING, "Albert Hall Museum", ["indoor", "culture"]),
                ],
            ),
        ],
        summary="Two days exploring Jaipur's heritage.",
    )


@pytest.fixture
def sample_trip(
    sample_itinerary: Itinerary,
    sample_preferences: Preferences,
    sample_constraints: Constraints,
    fake_user: AuthenticatedUser,
) -> Trip:
    now = datetime(2026, 5, 1, 12, 0, tzinfo=UTC)
    return Trip(
        trip_id="trip-1",
        owner_uid=fake_user.uid,
        preferences=sample_preferences,
        constraints=sample_constraints,
        itinerary=sample_itinerary,
        change_log=[],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture(autouse=True)
def _patch_firebase_init(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Prevent firebase-admin from talking to GCP during tests."""
    with patch("app.auth._ensure_firebase_initialized", lambda _settings: None):
        yield
