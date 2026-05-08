"""Trip repository — Firestore-backed persistence under users/{uid}/trips/{tripId}.

Implementation lands in Phase 3.
"""

from typing import Protocol

from app.models import Trip, TripSummary


class TripRepository(Protocol):
    async def create(self, trip: Trip) -> None: ...
    async def get(self, owner_uid: str, trip_id: str) -> Trip | None: ...
    async def list_for_user(
        self, owner_uid: str, limit: int, cursor: str | None
    ) -> list[TripSummary]: ...
    async def update(self, trip: Trip) -> None: ...
    async def delete(self, owner_uid: str, trip_id: str) -> bool: ...


class FirestoreTripRepository:
    """Real Firestore-backed implementation."""

    def __init__(self, project_id: str) -> None:
        self._project_id = project_id

    async def create(self, trip: Trip) -> None:
        raise NotImplementedError("FirestoreTripRepository.create implemented in Phase 3")

    async def get(self, owner_uid: str, trip_id: str) -> Trip | None:
        raise NotImplementedError("FirestoreTripRepository.get implemented in Phase 3")

    async def list_for_user(
        self, owner_uid: str, limit: int, cursor: str | None
    ) -> list[TripSummary]:
        raise NotImplementedError("FirestoreTripRepository.list_for_user implemented in Phase 3")

    async def update(self, trip: Trip) -> None:
        raise NotImplementedError("FirestoreTripRepository.update implemented in Phase 3")

    async def delete(self, owner_uid: str, trip_id: str) -> bool:
        raise NotImplementedError("FirestoreTripRepository.delete implemented in Phase 3")


class InMemoryTripRepository:
    """Test/dev double — keeps trips in a dict by (uid, trip_id)."""

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], Trip] = {}

    async def create(self, trip: Trip) -> None:
        self._store[(trip.owner_uid, trip.trip_id)] = trip

    async def get(self, owner_uid: str, trip_id: str) -> Trip | None:
        return self._store.get((owner_uid, trip_id))

    async def list_for_user(
        self, owner_uid: str, limit: int, cursor: str | None
    ) -> list[TripSummary]:
        items = [
            TripSummary(
                trip_id=trip.trip_id,
                destination=trip.constraints.destination,
                arrival_date=trip.constraints.arrival_date.isoformat(),
                departure_date=trip.constraints.departure_date.isoformat(),
                num_days=trip.constraints.num_days,
                created_at=trip.created_at,
                updated_at=trip.updated_at,
            )
            for (uid, _), trip in self._store.items()
            if uid == owner_uid
        ]
        items.sort(key=lambda s: s.updated_at, reverse=True)
        return items[:limit]

    async def update(self, trip: Trip) -> None:
        self._store[(trip.owner_uid, trip.trip_id)] = trip

    async def delete(self, owner_uid: str, trip_id: str) -> bool:
        return self._store.pop((owner_uid, trip_id), None) is not None
