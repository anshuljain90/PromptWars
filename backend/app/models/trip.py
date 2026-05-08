"""Trip aggregate: the persisted Firestore document."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.disruption import ChangeLogEntry
from app.models.itinerary import Itinerary
from app.models.preferences import Constraints, Preferences


class Trip(BaseModel):
    """A user's trip, persisted under users/{uid}/trips/{tripId}."""

    trip_id: str
    owner_uid: str
    preferences: Preferences
    constraints: Constraints
    itinerary: Itinerary
    change_log: list[ChangeLogEntry] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class TripSummary(BaseModel):
    """Lightweight projection used in trip-list responses."""

    trip_id: str
    destination: str
    arrival_date: str
    departure_date: str
    num_days: int
    created_at: datetime
    updated_at: datetime
