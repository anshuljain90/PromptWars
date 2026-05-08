"""Planner unit tests — verifies prompt assembly, caching, and error paths.

Gemini and Places are both fully mocked so tests run offline.
"""

from datetime import date
from pathlib import Path

import pytest

from app.clients.gemini import FakeGeminiClient
from app.clients.places import FixturePlacesClient
from app.models import Constraints, Itinerary, Preferences
from app.services.planner import Planner, PlannerError

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def places() -> FixturePlacesClient:
    return FixturePlacesClient(fixtures_dir=FIXTURES_DIR)


def _canned_itinerary() -> dict:
    return {
        "summary": "Two days in Jaipur covering history and food.",
        "days": [
            {
                "day_index": 1,
                "date_iso": "2026-06-01",
                "slots": [
                    {
                        "slot_id": "d1-m",
                        "period": "morning",
                        "place_id": "jpr-amber-fort",
                        "place_name": "Amber Fort",
                        "place_type": "fort",
                        "address": "Amber, Jaipur",
                        "lat": 26.9855,
                        "lng": 75.8513,
                        "description": "Hilltop fort with mirror palace.",
                        "duration_min": 180,
                        "estimated_cost_inr": 1100,
                        "rationale": "Anchors history interest with a flagship Jaipur monument.",
                        "tags": ["outdoor", "history"],
                    },
                    {
                        "slot_id": "d1-a",
                        "period": "afternoon",
                        "place_id": "jpr-city-palace",
                        "place_name": "City Palace",
                        "place_type": "palace",
                        "address": "Pink City, Jaipur",
                        "lat": 26.9258,
                        "lng": 75.8237,
                        "description": "Royal palace complex.",
                        "duration_min": 120,
                        "estimated_cost_inr": 800,
                        "rationale": "Indoor cultural visit balancing the morning fort.",
                        "tags": ["indoor", "history", "culture"],
                    },
                    {
                        "slot_id": "d1-e",
                        "period": "evening",
                        "place_id": "jpr-chokhi-dhani",
                        "place_name": "Chokhi Dhani",
                        "place_type": "restaurant",
                        "address": "Tonk Rd, Jaipur",
                        "lat": 26.7569,
                        "lng": 75.8330,
                        "description": "Rajasthani folk-village dining.",
                        "duration_min": 150,
                        "estimated_cost_inr": 2000,
                        "rationale": "Veg Rajasthani thali aligned with food interest.",
                        "tags": ["indoor", "food", "culture"],
                    },
                ],
            },
            {
                "day_index": 2,
                "date_iso": "2026-06-02",
                "slots": [
                    {
                        "slot_id": "d2-m",
                        "period": "morning",
                        "place_id": "jpr-hawa-mahal",
                        "place_name": "Hawa Mahal",
                        "place_type": "monument",
                        "address": "Pink City, Jaipur",
                        "lat": 26.9239,
                        "lng": 75.8267,
                        "description": "Pink-sandstone facade with screened windows.",
                        "duration_min": 90,
                        "estimated_cost_inr": 400,
                        "rationale": "Honors the must-see request and balanced pace.",
                        "tags": ["outdoor", "history"],
                    },
                    {
                        "slot_id": "d2-a",
                        "period": "afternoon",
                        "place_id": "jpr-jantar-mantar",
                        "place_name": "Jantar Mantar",
                        "place_type": "observatory",
                        "address": "Pink City, Jaipur",
                        "lat": 26.9248,
                        "lng": 75.8246,
                        "description": "UNESCO observatory with stone instruments.",
                        "duration_min": 90,
                        "estimated_cost_inr": 400,
                        "rationale": "History-rich UNESCO site near Hawa Mahal.",
                        "tags": ["outdoor", "history", "culture"],
                    },
                    {
                        "slot_id": "d2-e",
                        "period": "evening",
                        "place_id": "jpr-albert-hall",
                        "place_name": "Albert Hall Museum",
                        "place_type": "museum",
                        "address": "Ram Niwas Garden, Jaipur",
                        "lat": 26.9117,
                        "lng": 75.8198,
                        "description": "Indo-Saracenic museum with antiquities.",
                        "duration_min": 90,
                        "estimated_cost_inr": 400,
                        "rationale": "Indoor culture stop closing day two.",
                        "tags": ["indoor", "culture", "history"],
                    },
                ],
            },
        ],
    }


async def test_plan_returns_itinerary_for_valid_inputs(
    sample_preferences: Preferences,
    sample_constraints: Constraints,
    places: FixturePlacesClient,
) -> None:
    gemini = FakeGeminiClient(canned={"Itinerary": _canned_itinerary()})
    planner = Planner(gemini=gemini, places=places)

    itinerary = await planner.plan(sample_preferences, sample_constraints)

    assert isinstance(itinerary, Itinerary)
    assert len(itinerary.days) == 2
    all_slots = [s for d in itinerary.days for s in d.slots]
    assert all(s.rationale for s in all_slots)
    assert {s.place_id for s in all_slots} == {
        "jpr-amber-fort",
        "jpr-city-palace",
        "jpr-chokhi-dhani",
        "jpr-hawa-mahal",
        "jpr-jantar-mantar",
        "jpr-albert-hall",
    }


async def test_plan_passes_user_preferences_into_prompt(
    sample_preferences: Preferences,
    sample_constraints: Constraints,
    places: FixturePlacesClient,
) -> None:
    gemini = FakeGeminiClient(canned={"Itinerary": _canned_itinerary()})
    planner = Planner(gemini=gemini, places=places)

    await planner.plan(sample_preferences, sample_constraints)

    assert len(gemini.calls) == 1
    _system, user_prompt, _key = gemini.calls[0]
    assert "Jaipur" in user_prompt
    assert "history" in user_prompt
    assert "food" in user_prompt
    assert "Hawa Mahal" in user_prompt  # must-see propagated


async def test_plan_raises_when_no_candidates_found(
    sample_preferences: Preferences,
    places: FixturePlacesClient,
) -> None:
    nowhere = Constraints(
        destination="Atlantis",
        arrival_date=date(2026, 6, 1),
        departure_date=date(2026, 6, 4),
        travelers=2,
    )
    gemini = FakeGeminiClient()
    planner = Planner(gemini=gemini, places=places)

    with pytest.raises(PlannerError, match="No candidate places"):
        await planner.plan(sample_preferences, nowhere)


async def test_plan_uses_stable_cache_key_for_identical_inputs(
    sample_preferences: Preferences,
    sample_constraints: Constraints,
    places: FixturePlacesClient,
) -> None:
    gemini = FakeGeminiClient(canned={"Itinerary": _canned_itinerary()})
    planner = Planner(gemini=gemini, places=places)

    await planner.plan(sample_preferences, sample_constraints)
    await planner.plan(sample_preferences, sample_constraints)

    keys = [call[2] for call in gemini.calls]
    assert keys[0] == keys[1], "Identical inputs must produce identical cache keys"
