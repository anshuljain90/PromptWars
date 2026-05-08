"""Shared pytest fixtures: mocked external clients and an authed test client."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import date, datetime, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthenticatedUser, require_user
from app.clients.firestore import InMemoryTripRepository
from app.main import app
from app.models import (
    BudgetTier,
    Constraints,
    DietaryPreference,
    Day,
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
def authed_client(fake_user: AuthenticatedUser) -> Iterator[TestClient]:
    """A FastAPI TestClient with auth dependency overridden to a fixed test user."""

    async def _override() -> AuthenticatedUser:
        return fake_user

    app.dependency_overrides[require_user] = _override
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.pop(require_user, None)


@pytest.fixture
def unauthed_client() -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client


@pytest.fixture
def trip_repository() -> InMemoryTripRepository:
    return InMemoryTripRepository()


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
    now = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
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
