"""Trip CRUD + disruption injection routes.

Phase 1: skeleton with auth wiring only. Real handlers land in Phase 3 (CRUD)
and Phase 4 (disruption injection).
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import AuthenticatedUser, require_user
from app.models import Disruption, Trip, TripInput, TripSummary

router = APIRouter(prefix="/trips", tags=["trips"])


@router.get("", response_model=list[TripSummary])
async def list_trips(
    _user: AuthenticatedUser = Depends(require_user),
    limit: int = 20,
    cursor: str | None = None,
) -> list[TripSummary]:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "list_trips not yet implemented")


@router.post("", response_model=Trip, status_code=status.HTTP_201_CREATED)
async def create_trip(
    _payload: TripInput,
    _user: AuthenticatedUser = Depends(require_user),
) -> Trip:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "create_trip not yet implemented")


@router.get("/{trip_id}", response_model=Trip)
async def get_trip(
    trip_id: str,
    _user: AuthenticatedUser = Depends(require_user),
) -> Trip:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "get_trip not yet implemented")


@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trip(
    trip_id: str,
    _user: AuthenticatedUser = Depends(require_user),
) -> None:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "delete_trip not yet implemented")


@router.post("/{trip_id}/disruptions", response_model=Trip)
async def inject_disruption(
    trip_id: str,
    _disruption: Disruption,
    _user: AuthenticatedUser = Depends(require_user),
) -> Trip:
    raise HTTPException(status.HTTP_501_NOT_IMPLEMENTED, "inject_disruption not yet implemented")
