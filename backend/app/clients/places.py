"""Places client — Maps Places API with a fixture-backed alternative for tests/demos.

Implementation lands in Phase 2.
"""

from typing import Protocol

from pydantic import BaseModel, Field


class PlaceCandidate(BaseModel):
    """A normalized place returned by either the live or fixture backend."""

    place_id: str
    name: str
    place_type: str
    address: str = ""
    lat: float
    lng: float
    rating: float | None = None
    price_level: int | None = None
    tags: list[str] = Field(default_factory=list)
    photo_url: str | None = None


class PlacesClient(Protocol):
    async def search(
        self,
        destination: str,
        interests: list[str],
        limit: int = 30,
    ) -> list[PlaceCandidate]: ...

    async def details(self, place_id: str) -> PlaceCandidate | None: ...


class LivePlacesClient:
    """Real Maps Places API client with a TTL cache."""

    def __init__(self, api_key: str, cache_ttl_seconds: int = 3600) -> None:
        self._api_key = api_key
        self._cache_ttl = cache_ttl_seconds

    async def search(
        self,
        destination: str,
        interests: list[str],
        limit: int = 30,
    ) -> list[PlaceCandidate]:
        raise NotImplementedError("LivePlacesClient.search implemented in Phase 2")

    async def details(self, place_id: str) -> PlaceCandidate | None:
        raise NotImplementedError("LivePlacesClient.details implemented in Phase 2")


class FixturePlacesClient:
    """Reads pre-fetched JSON files under fixtures/places_{city}.json."""

    def __init__(self, fixtures_dir: str) -> None:
        self._fixtures_dir = fixtures_dir

    async def search(
        self,
        destination: str,
        interests: list[str],
        limit: int = 30,
    ) -> list[PlaceCandidate]:
        raise NotImplementedError("FixturePlacesClient.search implemented in Phase 2")

    async def details(self, place_id: str) -> PlaceCandidate | None:
        raise NotImplementedError("FixturePlacesClient.details implemented in Phase 2")
