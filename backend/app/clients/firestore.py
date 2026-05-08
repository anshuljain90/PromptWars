"""Trip repository — Firestore-backed persistence under users/{uid}/trips/{tripId}.

Uses the async Firestore client. Authorization is enforced both here (via the
user-scoped query path) AND in firestore.rules — defense in depth.
"""

from __future__ import annotations

import logging
from typing import Protocol

from google.cloud import firestore

from app.models import Trip, TripSummary

logger = logging.getLogger(__name__)


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
        if not project_id:
            raise ValueError("FIREBASE_PROJECT_ID is required for FirestoreTripRepository")
        self._client = firestore.AsyncClient(project=project_id)

    def _trips_collection(self, uid: str) -> firestore.AsyncCollectionReference:
        return self._client.collection("users").document(uid).collection("trips")

    async def create(self, trip: Trip) -> None:
        doc_ref = self._trips_collection(trip.owner_uid).document(trip.trip_id)
        await doc_ref.set(trip.model_dump(mode="json"))

    async def get(self, owner_uid: str, trip_id: str) -> Trip | None:
        snapshot = await self._trips_collection(owner_uid).document(trip_id).get()
        if not snapshot.exists:
            return None
        return Trip.model_validate(snapshot.to_dict())

    async def list_for_user(
        self, owner_uid: str, limit: int, cursor: str | None
    ) -> list[TripSummary]:
        query = (
            self._trips_collection(owner_uid)
            .order_by("updated_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        if cursor:
            cursor_snap = await self._trips_collection(owner_uid).document(cursor).get()
            if cursor_snap.exists:
                query = query.start_after(cursor_snap)
        docs = [doc async for doc in query.stream()]
        summaries: list[TripSummary] = []
        for doc in docs:
            trip = Trip.model_validate(doc.to_dict())
            summaries.append(
                TripSummary(
                    trip_id=trip.trip_id,
                    destination=trip.constraints.destination,
                    arrival_date=trip.constraints.arrival_date.isoformat(),
                    departure_date=trip.constraints.departure_date.isoformat(),
                    num_days=trip.constraints.num_days,
                    created_at=trip.created_at,
                    updated_at=trip.updated_at,
                )
            )
        return summaries

    async def update(self, trip: Trip) -> None:
        doc_ref = self._trips_collection(trip.owner_uid).document(trip.trip_id)
        await doc_ref.set(trip.model_dump(mode="json"), merge=False)

    async def delete(self, owner_uid: str, trip_id: str) -> bool:
        doc_ref = self._trips_collection(owner_uid).document(trip_id)
        snapshot = await doc_ref.get()
        if not snapshot.exists:
            return False
        await doc_ref.delete()
        return True


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
