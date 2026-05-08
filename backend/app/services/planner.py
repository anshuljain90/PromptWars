"""Initial itinerary planner — single Gemini call producing a structured Itinerary.

The planner has one responsibility: turn Preferences + Constraints into a typed
Itinerary using Gemini's structured output. It does not handle disruptions or
re-planning — those are separate roles (see services/replanner.py).
"""

from __future__ import annotations

import json
import logging

from app.clients.gemini import GeminiClient
from app.clients.places import PlaceCandidate, PlacesClient
from app.models import Constraints, Itinerary, Preferences

logger = logging.getLogger(__name__)


_SYSTEM_PROMPT = """You are an expert travel planner.
You produce structured day-by-day itineraries from user preferences and constraints.

Hard rules — never violate:
1. Use ONLY places from the provided candidate list. Use the place_id verbatim.
   Do not invent places, addresses, or coordinates.
2. Include every must-see place at least once across the trip.
3. Exclude every must-avoid place and category.
4. Each day has exactly one slot per period in this order: morning, afternoon, evening.
   You may omit one period for a relaxed pace.
5. Each slot's `rationale` must reference the user's stated preferences in plain
   English (e.g., "matches your history interest and mid-range budget").
6. Time-block guidance: morning 09:00-12:00, afternoon 13:00-17:00, evening 18:00-22:00.
7. Cost estimates in INR for two travelers unless specified otherwise.
8. Do not duplicate the same place_id across two slots.
9. `slot_id` format: "d{day_index}-{period_initial}" (e.g., "d1-m", "d1-a", "d2-e").
10. `tags` on each slot should reflect indoor/outdoor and the dominant interest
    (e.g., ["outdoor", "history"], ["indoor", "food"]).
"""


class Planner:
    """Generates a multi-day itinerary from preferences + constraints."""

    def __init__(self, gemini: GeminiClient, places: PlacesClient) -> None:
        self._gemini = gemini
        self._places = places

    async def plan(self, preferences: Preferences, constraints: Constraints) -> Itinerary:
        candidates = await self._places.search(
            destination=constraints.destination,
            interests=[i.value for i in preferences.interests],
            limit=40,
        )
        if not candidates:
            raise PlannerError(
                f"No candidate places found for destination {constraints.destination!r}"
            )
        user_prompt = _build_user_prompt(preferences, constraints, candidates)
        cache_key = _cache_key(preferences, constraints, candidates)
        try:
            return await self._gemini.generate_structured(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=Itinerary,
                cache_key=cache_key,
            )
        except Exception as exc:
            raise PlannerError(f"Failed to generate itinerary: {exc}") from exc


class PlannerError(RuntimeError):
    """Raised when itinerary generation cannot complete."""


def _build_user_prompt(
    preferences: Preferences,
    constraints: Constraints,
    candidates: list[PlaceCandidate],
) -> str:
    candidate_summaries = [
        {
            "place_id": p.place_id,
            "name": p.name,
            "type": p.place_type,
            "lat": p.lat,
            "lng": p.lng,
            "tags": p.tags,
            "rating": p.rating,
            "price_level": p.price_level,
        }
        for p in candidates
    ]
    payload = {
        "destination": constraints.destination,
        "arrival_date": constraints.arrival_date.isoformat(),
        "departure_date": constraints.departure_date.isoformat(),
        "num_days": constraints.num_days,
        "travelers": constraints.travelers,
        "group": preferences.group.value,
        "pace": preferences.pace.value,
        "budget": preferences.budget.value,
        "interests": [i.value for i in preferences.interests],
        "diet": preferences.dietary.value,
        "cuisines": preferences.cuisines,
        "mobility_notes": constraints.mobility_notes,
        "must_see": constraints.must_see,
        "must_avoid": constraints.must_avoid,
        "candidate_places": candidate_summaries,
    }
    return (
        "Generate a structured itinerary for the following trip. "
        "Pick the best places from the candidate list that match the user's "
        "preferences and constraints.\n\n" + json.dumps(payload, ensure_ascii=False, indent=2)
    )


def _cache_key(
    preferences: Preferences,
    constraints: Constraints,
    candidates: list[PlaceCandidate],
) -> str:
    """Stable key so identical inputs hit the cache regardless of dict order."""
    parts = {
        "preferences": preferences.model_dump(mode="json"),
        "constraints": constraints.model_dump(mode="json"),
        "candidate_ids": sorted(p.place_id for p in candidates),
    }
    return json.dumps(parts, sort_keys=True)
