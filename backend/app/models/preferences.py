"""Trip input: user preferences and hard constraints."""

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class Interest(StrEnum):
    CULTURE = "culture"
    FOOD = "food"
    ADVENTURE = "adventure"
    NATURE = "nature"
    NIGHTLIFE = "nightlife"
    SHOPPING = "shopping"
    HISTORY = "history"


class BudgetTier(StrEnum):
    BUDGET = "budget"
    MID_RANGE = "mid_range"
    LUXURY = "luxury"


class Pace(StrEnum):
    RELAXED = "relaxed"
    BALANCED = "balanced"
    PACKED = "packed"


class DietaryPreference(StrEnum):
    ANY = "any"
    VEG = "veg"
    NON_VEG = "non_veg"
    VEGAN = "vegan"


class GroupComposition(StrEnum):
    SOLO = "solo"
    COUPLE = "couple"
    FAMILY = "family"
    FRIENDS = "friends"


class Preferences(BaseModel):
    """Soft inputs that shape (but do not strictly bound) the itinerary."""

    interests: list[Interest] = Field(min_length=1, max_length=7)
    budget: BudgetTier
    pace: Pace
    dietary: DietaryPreference = DietaryPreference.ANY
    cuisines: list[str] = Field(default_factory=list, max_length=10)
    group: GroupComposition

    @field_validator("cuisines")
    @classmethod
    def _strip_cuisines(cls, value: list[str]) -> list[str]:
        return [c.strip() for c in value if c.strip()]


class Constraints(BaseModel):
    """Hard inputs that the itinerary must respect."""

    destination: str = Field(min_length=2, max_length=80)
    arrival_date: date
    departure_date: date
    travelers: int = Field(ge=1, le=20)
    mobility_notes: str = Field(default="", max_length=300)
    must_see: list[str] = Field(default_factory=list, max_length=20)
    must_avoid: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def _validate_dates(self) -> "Constraints":
        if self.departure_date <= self.arrival_date:
            raise ValueError("departure_date must be after arrival_date")
        if (self.departure_date - self.arrival_date).days > 14:
            raise ValueError("trip length must be 14 days or fewer (v1 scope)")
        return self

    @property
    def num_days(self) -> int:
        return (self.departure_date - self.arrival_date).days


class TripInput(BaseModel):
    """The combined request payload for creating a new trip."""

    preferences: Preferences
    constraints: Constraints
