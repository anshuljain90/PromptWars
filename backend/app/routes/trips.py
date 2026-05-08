"""Trip CRUD + disruption injection routes.

All routes require a verified Firebase ID token. Authorization (a user can only
access their own trips) is enforced by scoping every query/write to
request.state.user.uid.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.auth import AuthenticatedUser, require_user
from app.clients.firestore import TripRepository
from app.dependencies import get_classifier, get_planner, get_replanner, get_trip_repo
from app.models import (
    ChangeLogEntry,
    Disruption,
    Itinerary,
    Trip,
    TripInput,
    TripSummary,
)
from app.services.classifier import DisruptionClassifier
from app.services.planner import Planner, PlannerError
from app.services.replanner import Replanner, ReplannerError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("", response_model=list[TripSummary])
async def list_trips(
    user: AuthenticatedUser = Depends(require_user),
    repo: TripRepository = Depends(get_trip_repo),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None, max_length=128),
) -> list[TripSummary]:
    return await repo.list_for_user(owner_uid=user.uid, limit=limit, cursor=cursor)


@router.post("", response_model=Trip, status_code=status.HTTP_201_CREATED)
async def create_trip(
    payload: TripInput,
    user: AuthenticatedUser = Depends(require_user),
    repo: TripRepository = Depends(get_trip_repo),
    planner: Planner = Depends(get_planner),
) -> Trip:
    try:
        itinerary = await planner.plan(payload.preferences, payload.constraints)
    except PlannerError as exc:
        logger.warning("Planner failed for uid=%s: %s", user.uid, exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    now = datetime.now(UTC)
    trip = Trip(
        trip_id=uuid.uuid4().hex,
        owner_uid=user.uid,
        preferences=payload.preferences,
        constraints=payload.constraints,
        itinerary=itinerary,
        change_log=[],
        created_at=now,
        updated_at=now,
    )
    await repo.create(trip)
    return trip


@router.get("/{trip_id}", response_model=Trip)
async def get_trip(
    trip_id: str,
    user: AuthenticatedUser = Depends(require_user),
    repo: TripRepository = Depends(get_trip_repo),
) -> Trip:
    trip = await repo.get(owner_uid=user.uid, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trip not found")
    return trip


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_trip(
    trip_id: str,
    user: AuthenticatedUser = Depends(require_user),
    repo: TripRepository = Depends(get_trip_repo),
) -> Response:
    deleted = await repo.delete(owner_uid=user.uid, trip_id=trip_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trip not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{trip_id}/disruptions", response_model=Trip)
async def inject_disruption(
    trip_id: str,
    disruption: Disruption,
    user: AuthenticatedUser = Depends(require_user),
    repo: TripRepository = Depends(get_trip_repo),
    classifier: DisruptionClassifier = Depends(get_classifier),
    replanner: Replanner = Depends(get_replanner),
) -> Trip:
    """Apply a disruption — classify affected slots, patch them, update the trip.

    The whole pipeline is one server-side transaction-ish unit:
        classify → fetch alternatives + replan → write patched itinerary
                 + append change-log entry → Firestore push triggers UI listener.
    """
    trip = await repo.get(owner_uid=user.uid, trip_id=trip_id)
    if trip is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trip not found")

    classification = classifier.classify(trip.itinerary, disruption)
    if not classification.affected_slot_ids:
        # Nothing to re-plan — record an informational entry and return unchanged.
        entry = ChangeLogEntry(
            at=datetime.now(UTC),
            disruption_type=disruption.type,
            summary=classification.reasoning or "Disruption did not affect any slot.",
            affected_slot_ids=[],
            replaced_with=[],
        )
        trip = trip.model_copy(
            update={"change_log": [*trip.change_log, entry], "updated_at": entry.at}
        )
        await repo.update(trip)
        return trip

    try:
        patched = await replanner.patch(
            itinerary=trip.itinerary,
            affected_slot_ids=classification.affected_slot_ids,
            disruption=disruption,
        )
    except ReplannerError as exc:
        logger.warning("Replanner failed for trip=%s uid=%s: %s", trip_id, user.uid, exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc

    new_itinerary = _apply_patches(trip.itinerary, patched)
    entry = ChangeLogEntry(
        at=datetime.now(UTC),
        disruption_type=disruption.type,
        summary=classification.reasoning,
        affected_slot_ids=classification.affected_slot_ids,
        replaced_with=[s.place_id for s in patched],
    )
    trip = trip.model_copy(
        update={
            "itinerary": new_itinerary,
            "change_log": [*trip.change_log, entry],
            "updated_at": entry.at,
        }
    )
    await repo.update(trip)
    return trip


def _apply_patches(itinerary: Itinerary, patched_slots: list) -> Itinerary:
    """Returns a new Itinerary where each affected slot is replaced by its patch.

    Patched slots keep their original slot_id and period. Other slots are untouched.
    """
    by_slot_id = {slot.slot_id: slot for slot in patched_slots}
    new_days = []
    for day in itinerary.days:
        new_slots = [by_slot_id.get(slot.slot_id, slot) for slot in day.slots]
        new_days.append(day.model_copy(update={"slots": new_slots}))
    return itinerary.model_copy(update={"days": new_days})
