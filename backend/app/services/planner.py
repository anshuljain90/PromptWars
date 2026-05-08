"""Initial itinerary planner — single Gemini call producing a structured Itinerary.

Implementation lands in Phase 2.
"""

from app.clients.gemini import GeminiClient
from app.clients.places import PlacesClient
from app.models import Constraints, Itinerary, Preferences


class Planner:
    """Generates a multi-day itinerary from preferences + constraints."""

    def __init__(self, gemini: GeminiClient, places: PlacesClient) -> None:
        self._gemini = gemini
        self._places = places

    async def plan(self, preferences: Preferences, constraints: Constraints) -> Itinerary:
        """Produce an Itinerary honoring user preferences and hard constraints."""
        raise NotImplementedError("Planner.plan implemented in Phase 2")
