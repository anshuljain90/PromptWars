"""Itinerary domain: the structured day-by-day plan returned by the planner."""

from enum import StrEnum

from pydantic import BaseModel, Field


class SlotPeriod(StrEnum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"


class TravelLeg(BaseModel):
    """Travel between the previous slot and this one."""

    duration_min: int = Field(ge=0, le=600)
    distance_km: float = Field(ge=0, le=500)
    mode: str = Field(default="driving")


class ItinerarySlot(BaseModel):
    """One activity within a day."""

    slot_id: str = Field(min_length=1, max_length=64)
    period: SlotPeriod
    place_id: str
    place_name: str
    place_type: str
    address: str = ""
    lat: float
    lng: float
    description: str = Field(max_length=400)
    duration_min: int = Field(ge=15, le=600)
    estimated_cost_inr: int = Field(ge=0, le=200000)
    rationale: str = Field(min_length=5, max_length=400)
    tags: list[str] = Field(default_factory=list)
    travel_from_prev: TravelLeg | None = None


class Day(BaseModel):
    day_index: int = Field(ge=1, le=14)
    date_iso: str
    slots: list[ItinerarySlot] = Field(min_length=1, max_length=6)


class Itinerary(BaseModel):
    days: list[Day] = Field(min_length=1, max_length=14)
    summary: str = Field(default="", max_length=600)
