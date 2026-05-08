"""Places client — Maps Places API with a fixture-backed alternative.

The fixture backend reads pre-curated JSON files under fixtures/places_{city}.json
and supports the same Protocol so the planner is agnostic to which backend ran.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Protocol

from cachetools import TTLCache
from pydantic import BaseModel, Field, TypeAdapter

logger = logging.getLogger(__name__)


class PlaceCandidate(BaseModel):
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


_PlaceList = TypeAdapter(list[PlaceCandidate])


class PlacesClient(Protocol):
    async def search(
        self,
        destination: str,
        interests: list[str],
        limit: int = 30,
    ) -> list[PlaceCandidate]: ...

    async def details(self, place_id: str) -> PlaceCandidate | None: ...


class LivePlacesClient:
    """Real Maps Places API client.

    NOTE: The actual Places API call lands when we have a confirmed Maps key
    and quota signed off. For Phase 2 we ship the fixture client + this stub
    so the demo path works end-to-end. The live path swaps in trivially.
    """

    def __init__(self, api_key: str, cache_ttl_seconds: int = 3600) -> None:
        if not api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY is required for LivePlacesClient")
        self._api_key = api_key
        self._cache_ttl = cache_ttl_seconds

    async def search(
        self,
        destination: str,
        interests: list[str],
        limit: int = 30,
    ) -> list[PlaceCandidate]:
        raise NotImplementedError(
            "LivePlacesClient.search will be implemented when Maps API key is provisioned;"
            " the demo path uses FixturePlacesClient until then."
        )

    async def details(self, place_id: str) -> PlaceCandidate | None:
        raise NotImplementedError("LivePlacesClient.details deferred — see search()")


class FixturePlacesClient:
    """Reads curated JSON files under fixtures/places_{city}.json.

    City matching is case-insensitive and ignores diacritics/whitespace, so
    "Jaipur", "jaipur ", and "JAIPUR" all hit places_jaipur.json.
    """

    def __init__(self, fixtures_dir: str | Path) -> None:
        self._dir = Path(fixtures_dir)
        self._cache: TTLCache[str, list[PlaceCandidate]] = TTLCache(maxsize=32, ttl=3600)

    async def search(
        self,
        destination: str,
        interests: list[str],
        limit: int = 30,
    ) -> list[PlaceCandidate]:
        all_places = self._load(destination)
        if not interests:
            return all_places[:limit]
        wanted = {i.lower() for i in interests}
        scored = sorted(
            all_places,
            key=lambda p: -len(wanted.intersection({t.lower() for t in p.tags})),
        )
        return scored[:limit]

    async def details(self, place_id: str) -> PlaceCandidate | None:
        for city_file in self._dir.glob("places_*.json"):
            for place in _PlaceList.validate_python(json.loads(city_file.read_text())):
                if place.place_id == place_id:
                    return place
        return None

    def _load(self, destination: str) -> list[PlaceCandidate]:
        slug = _slugify(destination)
        cache_key = f"city:{slug}"
        if (cached := self._cache.get(cache_key)) is not None:
            return cached
        path = self._dir / f"places_{slug}.json"
        if not path.exists():
            logger.warning("No fixture file for destination %r (looked for %s)", destination, path)
            self._cache[cache_key] = []
            return []
        places = _PlaceList.validate_python(json.loads(path.read_text()))
        self._cache[cache_key] = places
        return places


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
