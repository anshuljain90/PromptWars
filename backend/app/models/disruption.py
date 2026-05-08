"""Disruption events that can trigger a real-time re-plan."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class DisruptionType(StrEnum):
    CLOSURE = "closure"
    TRAFFIC = "traffic"
    WEATHER = "weather"


class ClosureDisruption(BaseModel):
    type: Literal[DisruptionType.CLOSURE] = DisruptionType.CLOSURE
    place_id: str
    reason: str = Field(default="closed for maintenance", max_length=200)


class TrafficDisruption(BaseModel):
    type: Literal[DisruptionType.TRAFFIC] = DisruptionType.TRAFFIC
    from_slot_id: str
    to_slot_id: str
    reason: str = Field(default="severe congestion", max_length=200)


class WeatherDisruption(BaseModel):
    type: Literal[DisruptionType.WEATHER] = DisruptionType.WEATHER
    day_index: int = Field(ge=1, le=14)
    period: str
    condition: str = Field(default="thunderstorm", max_length=80)


Disruption = Annotated[
    ClosureDisruption | TrafficDisruption | WeatherDisruption,
    Field(discriminator="type"),
]


class ChangeLogEntry(BaseModel):
    """One historical record of a disruption applied to a trip."""

    at: datetime
    disruption_type: DisruptionType
    summary: str = Field(max_length=400)
    affected_slot_ids: list[str] = Field(default_factory=list)
    replaced_with: list[str] = Field(default_factory=list)
