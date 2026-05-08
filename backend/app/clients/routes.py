"""Maps Distance Matrix client — travel time + distance between two points.

Implementation lands in Phase 2.
"""

from typing import Protocol

from app.models.itinerary import TravelLeg


class RoutesClient(Protocol):
    async def leg(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: str = "driving",
    ) -> TravelLeg: ...


class LiveRoutesClient:
    def __init__(self, api_key: str, cache_ttl_seconds: int = 3600) -> None:
        self._api_key = api_key
        self._cache_ttl = cache_ttl_seconds

    async def leg(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: str = "driving",
    ) -> TravelLeg:
        raise NotImplementedError("LiveRoutesClient.leg implemented in Phase 2")


class FakeRoutesClient:
    """Returns deterministic fake travel legs for tests."""

    async def leg(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        mode: str = "driving",
    ) -> TravelLeg:
        # Crude haversine substitute — good enough for tests.
        return TravelLeg(duration_min=20, distance_km=8.0, mode=mode)
