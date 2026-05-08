"""Fixture-backed Places client — verifies offline planner inputs."""

from pathlib import Path

import pytest

from app.clients.places import FixturePlacesClient

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.fixture
def fixture_client() -> FixturePlacesClient:
    return FixturePlacesClient(fixtures_dir=FIXTURES_DIR)


async def test_search_returns_places_for_known_city(
    fixture_client: FixturePlacesClient,
) -> None:
    results = await fixture_client.search(destination="Jaipur", interests=[])
    assert len(results) > 0
    assert any(p.name == "Amber Fort" for p in results)
    for place in results:
        assert place.lat and place.lng
        assert place.place_id


async def test_search_is_case_insensitive(
    fixture_client: FixturePlacesClient,
) -> None:
    upper = await fixture_client.search(destination="JAIPUR", interests=[])
    lower = await fixture_client.search(destination="jaipur", interests=[])
    assert {p.place_id for p in upper} == {p.place_id for p in lower}


async def test_search_scores_places_by_interest_overlap(
    fixture_client: FixturePlacesClient,
) -> None:
    """Places with more matching interest tags rank higher."""
    results = await fixture_client.search(destination="Jaipur", interests=["food"])
    food_places = [p for p in results if "food" in [t.lower() for t in p.tags]]
    other_places = [p for p in results if "food" not in [t.lower() for t in p.tags]]
    if food_places and other_places:
        first_food_idx = next(i for i, p in enumerate(results) if p in food_places)
        first_other_idx = next(i for i, p in enumerate(results) if p in other_places)
        assert first_food_idx < first_other_idx


async def test_search_returns_empty_for_unknown_city(
    fixture_client: FixturePlacesClient,
) -> None:
    results = await fixture_client.search(destination="Atlantis", interests=["nature"])
    assert results == []


async def test_details_finds_known_place_id(
    fixture_client: FixturePlacesClient,
) -> None:
    place = await fixture_client.details("jpr-amber-fort")
    assert place is not None
    assert place.name == "Amber Fort"


async def test_details_returns_none_for_unknown_place(
    fixture_client: FixturePlacesClient,
) -> None:
    place = await fixture_client.details("does-not-exist")
    assert place is None


async def test_search_respects_limit(
    fixture_client: FixturePlacesClient,
) -> None:
    results = await fixture_client.search(destination="Jaipur", interests=[], limit=2)
    assert len(results) == 2
