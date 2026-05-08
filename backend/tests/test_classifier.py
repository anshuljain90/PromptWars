"""Disruption classifier — rule-based, deterministic, no LLM."""

from app.models import (
    ClosureDisruption,
    Itinerary,
    TrafficDisruption,
    WeatherDisruption,
)
from app.services.classifier import DisruptionClassifier


def test_closure_matches_slot_with_same_place_id(sample_itinerary: Itinerary) -> None:
    classifier = DisruptionClassifier()
    disruption = ClosureDisruption(place_id="pid-d1-m", reason="maintenance")

    result = classifier.classify(sample_itinerary, disruption)

    assert result.affected_slot_ids == ["d1-m"]
    assert "closed" in result.reasoning.lower()


def test_closure_returns_empty_when_place_not_in_itinerary(sample_itinerary: Itinerary) -> None:
    classifier = DisruptionClassifier()
    result = classifier.classify(sample_itinerary, ClosureDisruption(place_id="pid-not-here"))
    assert result.affected_slot_ids == []


def test_weather_affects_outdoor_slots_in_window(sample_itinerary: Itinerary) -> None:
    classifier = DisruptionClassifier()
    disruption = WeatherDisruption(day_index=2, period="afternoon", condition="thunderstorm")

    result = classifier.classify(sample_itinerary, disruption)

    assert result.affected_slot_ids == ["d2-a"]
    assert "thunderstorm" in result.reasoning.lower()


def test_weather_skips_indoor_slots(sample_itinerary: Itinerary) -> None:
    classifier = DisruptionClassifier()
    # Day 1 evening is Chokhi Dhani (indoor) — should NOT be affected.
    disruption = WeatherDisruption(day_index=1, period="evening", condition="thunderstorm")

    result = classifier.classify(sample_itinerary, disruption)

    assert result.affected_slot_ids == []


def test_weather_skips_other_days(sample_itinerary: Itinerary) -> None:
    classifier = DisruptionClassifier()
    # sample_itinerary covers days 1-2; day 5 is past the trip.
    disruption = WeatherDisruption(day_index=5, period="morning", condition="rain")
    result = classifier.classify(sample_itinerary, disruption)
    assert result.affected_slot_ids == []


def test_traffic_targets_destination_slot(sample_itinerary: Itinerary) -> None:
    classifier = DisruptionClassifier()
    disruption = TrafficDisruption(
        from_slot_id="d1-m", to_slot_id="d1-a", reason="severe congestion"
    )

    result = classifier.classify(sample_itinerary, disruption)

    assert result.affected_slot_ids == ["d1-a"]
    assert "blocked" in result.reasoning.lower()


def test_traffic_returns_empty_for_unknown_slot(sample_itinerary: Itinerary) -> None:
    classifier = DisruptionClassifier()
    disruption = TrafficDisruption(from_slot_id="x", to_slot_id="nope")
    result = classifier.classify(sample_itinerary, disruption)
    assert result.affected_slot_ids == []
