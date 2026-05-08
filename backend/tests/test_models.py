"""Validate the Pydantic boundary models — these contracts protect every module."""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models import (
    BudgetTier,
    ClosureDisruption,
    Constraints,
    DietaryPreference,
    DisruptionType,
    GroupComposition,
    Interest,
    Pace,
    Preferences,
    WeatherDisruption,
)


def test_constraints_rejects_inverted_dates() -> None:
    with pytest.raises(ValidationError):
        Constraints(
            destination="Jaipur",
            arrival_date=date(2026, 6, 4),
            departure_date=date(2026, 6, 1),
            travelers=2,
        )


def test_constraints_rejects_long_trip() -> None:
    with pytest.raises(ValidationError):
        Constraints(
            destination="Jaipur",
            arrival_date=date(2026, 6, 1),
            departure_date=date(2026, 7, 1),
            travelers=2,
        )


def test_constraints_num_days_property() -> None:
    c = Constraints(
        destination="Jaipur",
        arrival_date=date(2026, 6, 1),
        departure_date=date(2026, 6, 4),
        travelers=2,
    )
    assert c.num_days == 3


def test_preferences_requires_at_least_one_interest() -> None:
    with pytest.raises(ValidationError):
        Preferences(
            interests=[],
            budget=BudgetTier.BUDGET,
            pace=Pace.RELAXED,
            dietary=DietaryPreference.ANY,
            group=GroupComposition.SOLO,
        )


def test_disruption_discriminator_routes_to_correct_type() -> None:
    closure = ClosureDisruption(place_id="pid-1")
    assert closure.type == DisruptionType.CLOSURE

    weather = WeatherDisruption(day_index=2, period="afternoon")
    assert weather.type == DisruptionType.WEATHER
    assert weather.condition == "thunderstorm"


def test_interest_enum_accepts_canonical_values() -> None:
    assert Interest("history") == Interest.HISTORY
    assert Interest("food") == Interest.FOOD
